/**
 * CrossWire Incident Intelligence - Bangalore Monochrome Asset Animation Engine
 * Powered by GSAP (Greensock Animation Platform) & Minimalist UI Architecture
 * 
 * Strict performance guidelines:
 * - Uses hardware-accelerated transforms & opacities
 * - Zero layout thrashing
 * - Graceful fallback when GSAP is not yet loaded
 */

(function (window) {
  'use strict';

  const CrossWireMotion = {
    // Registry of active animations
    tweens: {},

    /**
     * Initialize all Bangalore SVG animations present on the current page
     */
    initAll: function () {
      if (!window.gsap) {
        console.warn('CrossWire Motion: GSAP not detected, retrying on load.');
        window.addEventListener('load', () => CrossWireMotion.initAll());
        return;
      }

      CrossWireMotion.initVidhanaSoudha();
      CrossWireMotion.initRadarScanner();
      CrossWireMotion.initMetroTransit();
      CrossWireMotion.initAutoRickshaw();
      CrossWireMotion.initRajakaluveFlow();
      CrossWireMotion.initDewateringPump();
      CrossWireMotion.initAudioVisualizer();
      CrossWireMotion.initPageEntrances();
    },

    /**
     * Vidhana Soudha Architectural Crest entrance & dome aura
     */
    initVidhanaSoudha: function () {
      const crests = document.querySelectorAll('.vidhana-soudha-vector');
      if (!crests.length) return;

      crests.forEach((crest) => {
        const dome = crest.querySelector('.gsap-dome');
        if (dome) {
          gsap.fromTo(dome, 
            { opacity: 0.7, strokeWidth: 1.5 },
            { opacity: 1, strokeWidth: 2.2, duration: 2.4, yoyo: true, repeat: -1, ease: "sine.inOut" }
          );
        }
      });
    },

    /**
     * KSNDMC Doppler Precipitation Radar - 360 deg sweep & Bellandur hotspot ping
     */
    initRadarScanner: function () {
      const sweeps = document.querySelectorAll('.gsap-radar-sweep');
      if (sweeps.length) {
        sweeps.forEach((sweep) => {
          gsap.to(sweep, {
            rotation: 360,
            duration: 3.6,
            repeat: -1,
            ease: "none",
            transformOrigin: "center center"
          });
        });
      }

      const pings = document.querySelectorAll('.gsap-ping-ring');
      if (pings.length) {
        pings.forEach((ping) => {
          gsap.fromTo(ping,
            { scale: 0.6, opacity: 1, transformOrigin: "center center" },
            { scale: 2.4, opacity: 0, duration: 1.8, repeat: -1, ease: "power1.out" }
          );
        });
      }

      const outerPings = document.querySelectorAll('.gsap-ping-ring-outer');
      if (outerPings.length) {
        outerPings.forEach((outer) => {
          gsap.fromTo(outer,
            { scale: 1, opacity: 0.8, transformOrigin: "center center" },
            { scale: 2.8, opacity: 0, duration: 2.2, repeat: -1, delay: 0.4, ease: "power2.out" }
          );
        });
      }
    },

    /**
     * Namma Metro Train - Horizontal glide over elevated viaduct
     */
    initMetroTransit: function () {
      const trains = document.querySelectorAll('.gsap-metro-train');
      if (!trains.length) return;

      trains.forEach((train) => {
        // Continuous smooth transit loop across the viaduct
        gsap.fromTo(train,
          { x: -180 },
          {
            x: 220,
            duration: 10,
            repeat: -1,
            ease: "power1.inOut",
            repeatDelay: 1.5,
            yoyo: false
          }
        );

        // Headlight subtle blink/beam
        const headlight = train.querySelector('.gsap-headlight');
        if (headlight) {
          gsap.to(headlight, {
            opacity: 0.3,
            duration: 0.8,
            repeat: -1,
            yoyo: true,
            ease: "steps(2)"
          });
        }
      });
    },

    /**
     * Bengaluru Auto-Rickshaw - Spinning wheels, wiper & suspension bob
     */
    initAutoRickshaw: function () {
      const autos = document.querySelectorAll('.bangalore-auto-vector');
      if (!autos.length) return;

      autos.forEach((auto) => {
        const frontWheel = auto.querySelector('.gsap-auto-wheel-front');
        const rearWheel = auto.querySelector('.gsap-auto-wheel-rear');
        const autoBody = auto.querySelector('.gsap-auto-body');
        const wiper = auto.querySelector('.gsap-auto-wiper');

        if (frontWheel) {
          gsap.to(frontWheel, {
            rotation: 360,
            duration: 1.2,
            repeat: -1,
            ease: "none",
            transformOrigin: "center center"
          });
        }

        if (rearWheel) {
          gsap.to(rearWheel, {
            rotation: 360,
            duration: 1.2,
            repeat: -1,
            ease: "none",
            transformOrigin: "center center"
          });
        }

        if (autoBody) {
          gsap.to(autoBody, {
            y: -1.5,
            duration: 0.35,
            repeat: -1,
            yoyo: true,
            ease: "sine.inOut"
          });
        }

        if (wiper) {
          gsap.fromTo(wiper,
            { rotation: -20, transformOrigin: "bottom left" },
            { rotation: 35, duration: 0.65, repeat: -1, yoyo: true, ease: "power1.inOut" }
          );
        }
      });
    },

    /**
     * Rajakaluve Canal Drainage - Water flow dash arrays & sensor ultrasonic pulses
     */
    initRajakaluveFlow: function () {
      // Streamline 1
      const stream1 = document.querySelectorAll('.gsap-streamline-1');
      if (stream1.length) {
        gsap.to(stream1, {
          strokeDashoffset: -50,
          duration: 1.5,
          repeat: -1,
          ease: "none"
        });
      }

      // Streamline 2
      const stream2 = document.querySelectorAll('.gsap-streamline-2');
      if (stream2.length) {
        gsap.to(stream2, {
          strokeDashoffset: -60,
          duration: 1.8,
          repeat: -1,
          ease: "none"
        });
      }

      // Sensor ultrasonic pings
      const ping1 = document.querySelectorAll('.gsap-sensor-ping-1');
      const ping2 = document.querySelectorAll('.gsap-sensor-ping-2');
      if (ping1.length) {
        gsap.to(ping1, {
          y: 8,
          opacity: 0,
          duration: 1.2,
          repeat: -1,
          ease: "power1.in"
        });
      }
      if (ping2.length) {
        gsap.to(ping2, {
          y: 12,
          opacity: 0,
          duration: 1.4,
          repeat: -1,
          delay: 0.3,
          ease: "power1.in"
        });
      }

      // Water surface wave motion
      const surface = document.querySelectorAll('.gsap-water-surface');
      if (surface.length) {
        gsap.to(surface, {
          y: -2,
          duration: 1.4,
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut"
        });
      }
    },

    /**
     * Dewatering Pump - Impeller spin, pressure gauge jitter, flow lines
     */
    initDewateringPump: function () {
      const impellers = document.querySelectorAll('.gsap-pump-impeller');
      if (impellers.length) {
        gsap.to(impellers, {
          rotation: 360,
          duration: 0.8,
          repeat: -1,
          ease: "none",
          transformOrigin: "center center"
        });
      }

      const gauges = document.querySelectorAll('.gsap-gauge-needle');
      if (gauges.length) {
        gsap.to(gauges, {
          rotation: 25,
          duration: 0.4,
          repeat: -1,
          yoyo: true,
          ease: "rough({strength: 1.5, points: 10, randomize: true})"
        });
      }

      const intakeFlow = document.querySelectorAll('.gsap-intake-flow');
      if (intakeFlow.length) {
        gsap.to(intakeFlow, {
          strokeDashoffset: -40,
          duration: 1.0,
          repeat: -1,
          ease: "none"
        });
      }

      const dischargeFlow = document.querySelectorAll('.gsap-discharge-flow');
      if (dischargeFlow.length) {
        gsap.to(dischargeFlow, {
          strokeDashoffset: -50,
          duration: 0.9,
          repeat: -1,
          ease: "none"
        });
      }

      const exhaust = document.querySelectorAll('.gsap-exhaust-puff');
      if (exhaust.length) {
        gsap.fromTo(exhaust,
          { y: 0, opacity: 1, scale: 0.8 },
          { y: -10, opacity: 0, scale: 1.8, duration: 0.9, repeat: -1, ease: "power1.out" }
        );
      }
    },

    /**
     * Sarvam Kannada Audio Waveform Oscillating Bars
     */
    initAudioVisualizer: function () {
      const waveform = document.querySelector('.audio-waveform-vector');
      if (!waveform) return;

      const bars = waveform.querySelectorAll('.wave-bar');
      if (!bars.length) return;

      // Keep reference to timeline
      window._crossWireAudioTl = gsap.timeline({ paused: true, repeat: -1, yoyo: true });
      bars.forEach((bar, index) => {
        const randomScale = 0.4 + Math.random() * 1.4;
        window._crossWireAudioTl.to(bar, {
          scaleY: randomScale,
          transformOrigin: "center center",
          duration: 0.2 + (index % 4) * 0.08,
          ease: "sine.inOut"
        }, index * 0.02);
      });
    },

    /**
     * Hook to play/pause audio visualizer
     */
    toggleAudioAnimation: function (isPlaying) {
      if (window._crossWireAudioTl) {
        if (isPlaying) {
          window._crossWireAudioTl.play();
        } else {
          window._crossWireAudioTl.pause();
          // Reset bars gracefully
          gsap.to('.wave-bar', { scaleY: 1, duration: 0.3 });
        }
      }
    },

    /**
     * Subtle Staggered Entrance Animations across pages
     */
    initPageEntrances: function () {
      const hero = document.querySelector('#hero-guide, section.border-2.border-black');
      if (hero) {
        gsap.from(hero, { y: 16, opacity: 0, duration: 0.5, ease: "power2.out" });
      }

      const stepCards = document.querySelectorAll('.step-card');
      if (stepCards.length) {
        gsap.from(stepCards, {
          y: 12,
          opacity: 0,
          stagger: 0.05,
          duration: 0.4,
          delay: 0.1,
          ease: "power2.out"
        });
      }

      // Initialize Card Hover Physics & Button Tactile Feedback
      CrossWireMotion.initHoverAndTactile();

      // Initialize GSAP High-FPS Custom Cursor & Magnetic Interactions
      CrossWireMotion.initCustomCursor();

      // Initialize ScrollTrigger & Smooth Scroll Progress
      CrossWireMotion.initScrollTriggers();
    },

    /**
     * GPU-Accelerated Card Hover Physics and Tactile Button Feedback
     */
    initHoverAndTactile: function () {
      // Tactile push on all actionable buttons and links
      const interactives = document.querySelectorAll('button, a.inline-block, .step-card, .vector-card');
      interactives.forEach((el) => {
        el.addEventListener('mousedown', () => {
          gsap.to(el, { scale: 0.98, duration: 0.1, ease: "power1.out" });
        });
        el.addEventListener('mouseup', () => {
          gsap.to(el, { scale: 1.0, duration: 0.2, ease: "back.out(2)" });
        });
        el.addEventListener('mouseleave', () => {
          gsap.to(el, { scale: 1.0, duration: 0.2, ease: "power1.out" });
        });
      });
    },

    /**
     * GSAP High-FPS Custom Cursor & Magnetic Micro-Interactions (quickTo pattern)
     */
    initCustomCursor: function () {
      // Skip on touch-only devices
      if (window.matchMedia && window.matchMedia('(pointer: coarse)').matches) {
        return;
      }

      let dot = document.getElementById('crosswire-cursor-dot');
      let ring = document.getElementById('crosswire-cursor-ring');

      if (!dot) {
        dot = document.createElement('div');
        dot.id = 'crosswire-cursor-dot';
        document.body.appendChild(dot);
      }
      if (!ring) {
        ring = document.createElement('div');
        ring.id = 'crosswire-cursor-ring';
        document.body.appendChild(ring);
      }

      // Initial offscreen placement
      gsap.set([dot, ring], { xPercent: -50, yPercent: -50, opacity: 0 });

      // High-FPS quickTo pipes (never call gsap.to in mousemove directly)
      const xDotTo = gsap.quickTo(dot, "x", { duration: 0.08, ease: "power2.out" });
      const yDotTo = gsap.quickTo(dot, "y", { duration: 0.08, ease: "power2.out" });
      const xRingTo = gsap.quickTo(ring, "x", { duration: 0.28, ease: "power3.out" });
      const yRingTo = gsap.quickTo(ring, "y", { duration: 0.28, ease: "power3.out" });

      let cursorVisible = false;

      window.addEventListener('mousemove', (e) => {
        if (!cursorVisible) {
          gsap.to([dot, ring], { opacity: 1, duration: 0.3, ease: "power2.out" });
          cursorVisible = true;
        }
        xDotTo(e.clientX);
        yDotTo(e.clientY);
        xRingTo(e.clientX);
        yRingTo(e.clientY);
      });

      window.addEventListener('mouseleave', () => {
        gsap.to([dot, ring], { opacity: 0, duration: 0.3, ease: "power2.out" });
        cursorVisible = false;
      });

      // Hover expansion on interactive elements
      const hoverTargets = document.querySelectorAll('a, button, input, .step-card, [data-hover], .vector-card, object, img');
      hoverTargets.forEach((target) => {
        target.addEventListener('mouseenter', () => {
          gsap.to(ring, {
            scale: 1.6,
            borderColor: '#111111',
            backgroundColor: 'rgba(17, 17, 17, 0.06)',
            duration: 0.25,
            ease: 'power2.out'
          });
          gsap.to(dot, { scale: 0.6, duration: 0.2, ease: 'power2.out' });
        });

        target.addEventListener('mouseleave', () => {
          gsap.to(ring, {
            scale: 1.0,
            borderColor: 'rgba(17, 17, 17, 0.45)',
            backgroundColor: 'transparent',
            duration: 0.25,
            ease: 'power2.out'
          });
          gsap.to(dot, { scale: 1.0, duration: 0.2, ease: 'power2.out' });
        });
      });

      // Mouse down / click snap
      window.addEventListener('mousedown', () => {
        gsap.to(ring, { scale: 0.85, duration: 0.12, ease: "power2.out" });
        gsap.to(dot, { scale: 1.3, duration: 0.12, ease: "power2.out" });
      });

      window.addEventListener('mouseup', () => {
        gsap.to(ring, { scale: 1.0, duration: 0.25, ease: "back.out(2)" });
        gsap.to(dot, { scale: 1.0, duration: 0.2, ease: "power2.out" });
      });

      // Magnetic Micro-Interactions on primary buttons
      const magneticButtons = document.querySelectorAll('button, a.inline-block, .magnetic-target');
      magneticButtons.forEach((btn) => {
        const xBtnTo = gsap.quickTo(btn, "x", { duration: 0.35, ease: "power3.out" });
        const yBtnTo = gsap.quickTo(btn, "y", { duration: 0.35, ease: "power3.out" });

        btn.addEventListener("mousemove", (e) => {
          const rect = btn.getBoundingClientRect();
          const x = (e.clientX - (rect.left + rect.width / 2)) * 0.2;
          const y = (e.clientY - (rect.top + rect.height / 2)) * 0.2;
          xBtnTo(x);
          yBtnTo(y);
        });

        btn.addEventListener("mouseleave", () => {
          xBtnTo(0);
          yBtnTo(0);
        });
      });
    },

    /**
     * ScrollTrigger Scroll Progress & Smooth Dynamic Reveals
     */
    initScrollTriggers: function () {
      if (!window.ScrollTrigger) return;
      gsap.registerPlugin(ScrollTrigger);

      // 1. Reading Progress Hairline Bar at Top
      let progressBar = document.getElementById('crosswire-scroll-bar');
      if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.id = 'crosswire-scroll-bar';
        document.body.appendChild(progressBar);
      }

      gsap.to(progressBar, {
        scaleX: 1,
        ease: "none",
        scrollTrigger: {
          trigger: document.documentElement,
          start: "top top",
          end: "bottom bottom",
          scrub: 0.3
        }
      });

      // 2. Smooth Section & Bento Card Ingress Reveals
      const scrollSections = document.querySelectorAll('main > section, .highlight-box, .highlight-card');
      scrollSections.forEach((section) => {
        gsap.fromTo(section, 
          { y: 20, opacity: 0.7 },
          {
            y: 0,
            opacity: 1,
            duration: 0.7,
            ease: "power2.out",
            scrollTrigger: {
              trigger: section,
              start: "top 92%",
              toggleActions: "play none none none",
              once: true
            }
          }
        );
      });

      // 3. Subtle Parallax for Bangalore Documentary Photography
      const photos = document.querySelectorAll('img.contrast-110, img.contrast-115, .group-hover\\:scale-105');
      photos.forEach((photo) => {
        gsap.fromTo(photo,
          { yPercent: -3 },
          {
            yPercent: 3,
            ease: "none",
            scrollTrigger: {
              trigger: photo,
              start: "top bottom",
              end: "bottom top",
              scrub: 1.2
            }
          }
        );
      });
    }
  };

  // Expose to window
  window.CrossWireMotion = CrossWireMotion;

  // Auto initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', CrossWireMotion.initAll);
  } else {
    CrossWireMotion.initAll();
  }

})(window);
