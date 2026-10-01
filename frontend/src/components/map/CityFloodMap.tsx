import { FC, useEffect, useRef } from 'react';
import L from 'leaflet';
import { Incident, Ticket } from '../../types/api';

interface CityFloodMapProps {
  incident: Incident | null;
  tickets: Ticket[];
}

export const CityFloodMap: FC<CityFloodMapProps> = ({ incident, tickets }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const centerLat = incident?.centroid[0] ?? 12.928;
    const centerLon = incident?.centroid[1] ?? 77.682;

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
      if (layer instanceof L.Marker || layer instanceof L.Circle || layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // Add Incident Centroid Circle
    if (incident) {
      L.circle(incident.centroid, {
        color: '#111111',
        fillColor: '#111111',
        fillOpacity: 0.12,
        radius: 450,
        weight: 2.5,
      })
        .bindPopup(`<strong>Incident Centroid: ${incident.id}</strong><br/>Active Hex Cells: ${incident.cells.join(', ')}`)
        .addTo(map);
    }

    // Add Ticket Markers
    tickets.forEach((t) => {
      const marker = L.circleMarker([t.lat, t.lon], {
        radius: 7,
        color: '#111111',
        fillColor: '#FFFFFF',
        fillOpacity: 1,
        weight: 2,
      });
      marker.bindPopup(`<strong>${t.id}</strong><br/>${t.text_en}<br/>Depth: ${t.photo_depth || 'N/A'}`);
      marker.addTo(map);
    });

    return () => {
      // Map instance cleanup on full unmount
    };
  }, [incident, tickets]);

  return (
    <div className="space-y-6">
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
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
            <div>Centroid: {incident ? `${incident.centroid[0].toFixed(3)}, ${incident.centroid[1].toFixed(3)}` : 'N/A'}</div>
            <div>Active Cells: {incident?.cells.length ?? 0} H3_R8</div>
          </div>
        </div>

        <p className="text-sm text-textBody leading-relaxed max-w-4xl">
          Monochrome architectural cartography displaying low-lying basin contours, stormwater canal (Rajakaluve) vectors, and vulnerable civil installations.
        </p>

        {/* Map Container with Strict Containment */}
        <div className="border-2 border-black h-[520px] w-full relative overflow-hidden bg-bone isolate">
          <div ref={mapContainerRef} className="w-full h-full" />
        </div>

        <div className="pt-3 border-t border-borderSubtle flex flex-wrap items-center justify-between text-xs font-mono text-textMuted">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border-2 border-black bg-white inline-block" /> Citizen Ticket Location
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 border-2 border-black bg-black/20 inline-block" /> Incident Basin Perimeter
            </span>
          </div>
          <span>Tile: Grayscale OpenStreetMap Architecture Layer (Zero Watermark)</span>
        </div>
      </div>
    </div>
  );
};
