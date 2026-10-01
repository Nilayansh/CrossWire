import { FC, useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Incident, Ticket } from '../../types/api';
import { fetchTrafficFlow } from '../../api/client';
import { Activity } from 'lucide-react';

interface CityFloodMapProps {
  incident: Incident | null;
  tickets: Ticket[];
}

const CRITICAL_INFRASTRUCTURE = [
  {
    name: 'Sakra World Hospital',
    type: 'hospital',
    coords: [12.9261, 77.6838] as [number, number],
    icon: '🏥',
    desc: 'Critical emergency care corridor along Outer Ring Road',
  },
  {
    name: 'Manipal Hospital Sarjapur',
    type: 'hospital',
    coords: [12.9185, 77.6715] as [number, number],
    icon: '🏥',
    desc: 'Secondary medical emergency route',
  },
  {
    name: 'Kadubeesanahalli 11kV Substation',
    type: 'substation',
    coords: [12.9362, 77.6934] as [number, number],
    icon: '⚡',
    desc: 'Feeder F-KADU-04 powering tech parks & Bellandur STP wet well',
  },
  {
    name: 'Bellandur STP Primary Pumping Station',
    type: 'stp',
    coords: [12.9340, 77.6720] as [number, number],
    icon: '🌊',
    desc: 'BWSSB Wastewater treatment intake & lake weir',
  },
  {
    name: 'Greenwood High School',
    type: 'school',
    coords: [12.9230, 77.6775] as [number, number],
    icon: '🏫',
    desc: 'School bus transit corridor',
  },
];

const CATEGORY_COLORS: Record<string, string> = {
  waterlogging: '#0284c7', // Sky Blue
  power: '#eab308',        // Yellow
  sewage: '#78350f',       // Brown
  traffic: '#ea580c',      // Orange
  solid_waste: '#475569',  // Slate
  road_damage: '#dc2626',  // Red
};

export const CityFloodMap: FC<CityFloodMapProps> = ({ incident, tickets }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const [trafficData, setTrafficData] = useState<{
    current_speed: number;
    free_flow_speed: number;
    speed_ratio: number;
    congestion: string;
    summary: string;
  } | null>(null);
  const [loadingTraffic, setLoadingTraffic] = useState(false);
  const [showTrafficLayer, setShowTrafficLayer] = useState(true);

  const centerLat = incident?.centroid[0] ?? 12.927;
  const centerLon = incident?.centroid[1] ?? 77.684;

  // Query live TomTom traffic flow
  const loadLiveTraffic = async () => {
    setLoadingTraffic(true);
    try {
      const data = await fetchTrafficFlow(centerLat, centerLon);
      setTrafficData(data);
    } catch (e) {
      console.warn('TomTom traffic notice:', e);
    } finally {
      setLoadingTraffic(false);
    }
  };

  useEffect(() => {
    loadLiveTraffic();
  }, [centerLat, centerLon]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [centerLat, centerLon],
        zoom: 14,
        zoomControl: true,
      });

      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        className: 'mono-tiles',
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      mapInstanceRef.current = map;
    } else {
      mapInstanceRef.current.setView([centerLat, centerLon], 14);
    }

    const map = mapInstanceRef.current;

    // Clear existing dynamic layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Circle || layer instanceof L.CircleMarker || layer instanceof L.Polyline) {
        map.removeLayer(layer);
      }
    });

    // 1. Draw H3 Spatial Cluster Disks (~460m radius for H3 resolution 8)
    if (incident) {
      incident.cells.forEach((cell, idx) => {
        L.circle(incident.centroid, {
          color: '#000000',
          fillColor: '#000000',
          fillOpacity: 0.08,
          radius: 460 + idx * 20,
          weight: 2,
          dashArray: '5, 5',
        })
          .bindPopup(`<strong>H3 Spatial Cell: ${cell}</strong><br/>Cluster ID: ${incident.id}<br/>Resolution: 8 (~461m radius)`)
          .addTo(map);
      });
    }

    // 2. Draw Live TomTom Traffic Arterial Corridor Line
    if (showTrafficLayer) {
      const orrCorridor: [number, number][] = [
        [12.918, 77.671], // Sarjapur Rd junction
        [12.926, 77.683], // EcoSpace ORR
        [12.928, 77.681], // Central Mall Flyover
        [12.936, 77.693], // Kadubeesanahalli
        [12.956, 77.701], // Marathahalli Bridge
      ];

      const trafficColor = trafficData?.congestion === 'heavy' ? '#dc2626' : trafficData?.congestion === 'moderate' ? '#ea580c' : '#16a34a';

      L.polyline(orrCorridor, {
        color: trafficColor,
        weight: 6,
        opacity: 0.85,
        lineCap: 'round',
      })
        .bindPopup(`<strong>TomTom Flow Arterial Line (ORR)</strong><br/>${trafficData?.summary || 'Congested corridor'}`)
        .addTo(map);
    }

    // 3. Draw Critical Infrastructure Nodes
    CRITICAL_INFRASTRUCTURE.forEach((node) => {
      const customIcon = L.divIcon({
        className: 'infra-marker',
        html: `<div style="background: white; border: 2px solid black; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">${node.icon}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      L.marker(node.coords, { icon: customIcon })
        .bindPopup(`<strong>${node.name}</strong><br/><span style="font-size:11px; color:#555;">${node.desc}</span>`)
        .addTo(map);
    });

    // 4. Draw Individual Citizen Ticket Pins (Color-coded by category)
    tickets.forEach((t) => {
      const color = CATEGORY_COLORS[t.category] || '#111111';
      const marker = L.circleMarker([t.lat, t.lon], {
        radius: 7 + (t.severity * 1.5),
        color: '#000000',
        fillColor: color,
        fillOpacity: 0.9,
        weight: 2,
      });

      const depthHtml = t.photo_depth ? `<br/><b>Water Depth:</b> ${t.photo_depth.toUpperCase()}` : '';
      const photoHtml = t.image_data ? `<br/><img src="${t.image_data}" style="width:100%; max-height:90px; object-fit:cover; margin-top:4px;" />` : '';

      marker.bindPopup(`
        <div style="font-family: monospace; font-size: 11px;">
          <strong style="font-size: 12px;">${t.id} (${t.category.toUpperCase()})</strong><br/>
          <span>${t.text_en || t.text_original}</span>
          ${depthHtml}
          ${photoHtml}
          <br/><span style="color:#777;">Severity: ${t.severity}/5 | Cell: ${t.h3_r8.slice(0, 8)}...</span>
        </div>
      `);
      marker.addTo(map);
    });
  }, [incident, tickets, showTrafficLayer, trafficData]);

  return (
    <div className="space-y-6">
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              Geographic Diagnostic View
            </span>
            <h2 className="text-2xl md:text-3xl font-serif font-bold italic text-black tracking-tight mt-1 max-w-5xl">
              Bellandur Drainage Basin & Infrastructure Overlays
            </h2>
          </div>
          <div className="text-xs font-mono text-right text-textMuted">
            <div>Centroid: {centerLat.toFixed(4)}, {centerLon.toFixed(4)}</div>
            <div>Cluster: {tickets.length} Geocoded Tickets</div>
          </div>
        </div>

        {/* Live TomTom Telemetry Banner */}
        <div className="border border-black bg-bone p-3.5 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-black shrink-0" />
            <div className="text-xs font-mono">
              <span className="font-bold text-black uppercase">TomTom Traffic Flow Telemetry: </span>
              {trafficData ? (
                <span className="text-textBody">
                  Current: <b>{trafficData.current_speed} km/h</b> (Freeflow: {trafficData.free_flow_speed} km/h) &bull;{' '}
                  <span className={`font-bold uppercase ${trafficData.congestion === 'heavy' ? 'text-red-600' : 'text-amber-600'}`}>
                    {trafficData.congestion} Congestion ({Math.round(trafficData.speed_ratio * 100)}% of normal)
                  </span>
                </span>
              ) : (
                <span className="text-textMuted">Querying live TomTom API for Bellandur Outer Ring Road corridor...</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => setShowTrafficLayer(!showTrafficLayer)}
              className="border border-black px-2.5 py-1 text-xs font-mono bg-white hover:bg-black hover:text-white transition-colors cursor-pointer"
            >
              {showTrafficLayer ? 'Hide Traffic Line' : 'Show Traffic Line'}
            </button>
            <button
              onClick={loadLiveTraffic}
              disabled={loadingTraffic}
              className="border border-black px-2.5 py-1 text-xs font-mono bg-black text-white hover:bg-white hover:text-black transition-colors cursor-pointer"
            >
              {loadingTraffic ? 'Querying...' : '↻ Refresh TomTom'}
            </button>
          </div>
        </div>

        {/* Map Container */}
        <div className="border-2 border-black h-[540px] w-full relative overflow-hidden bg-bone isolate">
          <div ref={mapContainerRef} className="w-full h-full" />
        </div>

        {/* Legend */}
        <div className="pt-3 border-t border-borderSubtle flex flex-wrap items-center justify-between text-xs font-mono text-textMuted gap-3">
          <div className="flex flex-wrap items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#0284c7] inline-block border border-black" /> Waterlogging
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#eab308] inline-block border border-black" /> BESCOM Power
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#78350f] inline-block border border-black" /> BWSSB Sewage
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#ea580c] inline-block border border-black" /> Traffic Stagnation
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border-2 border-dashed border-black bg-black/10 inline-block" /> H3 Hexagon Boundary
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-4 h-1.5 bg-red-600 inline-block" /> TomTom Arterial Slowdown
            </span>
          </div>
          <span>Tiles: OpenStreetMap Architecture Canvas &bull; Coordinates: EPSG:3857</span>
        </div>
      </div>
    </div>
  );
};
