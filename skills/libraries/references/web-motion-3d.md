# Motion, 3D, canvas and audio for the web

CSS transitions, keyframes, scroll-driven animations and the View Transitions API cover hover states, enter and exit, and page transitions without a dependency: reach for a library when the motion needs sequencing, physics, gestures or layout animation. Every animation respects `prefers-reduced-motion`. Names are npm packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Timelines, scroll-driven scenes, SVG morphing, text splitting | `gsap` (with ScrollTrigger) | `animejs` | GSAP is free under its own "no charge" licence, not an open-source one: read it before using it in a product that competes with Webflow. Anime.js is MIT |
| UI animation in React: layout, gestures, enter and exit, springs | `motion` | | Formerly Framer Motion; also has a plain JavaScript API |
| Animating list changes with no code | `@formkit/auto-animate` | | |
| Smooth scrolling | `lenis` | | Check keyboard and screen-reader scrolling still work |
| Designer-made vector animation | `@lottiefiles/dotlottie-web` | `lottie-web` | dotLottie files are smaller |
| Interactive vector animation with state machines | `@rive-app/canvas` | | Made in the Rive editor |
| Animated numbers | `@number-flow/react` | | |
| 3D | `three` | `@babylonjs/core` | Babylon.js brings a full engine: physics, GUI, inspector |
| 3D in React | `@react-three/fiber` with `@react-three/drei` | | Client-only; load it lazily |
| 2D canvas and WebGL sprites | `pixi.js` | | |
| Creative coding sketches | `p5` | | LGPL-2.1 |
| Particles | `@tsparticles/engine` | | |
| Animation editor for 3D scenes | `@theatre/core` | | Last release 2024-05 |
| 2D physics | `matter-js` | | Last release 2024-06 |
| 3D physics | `@dimforge/rapier3d` | | WebAssembly |
| Audio playback | `howler` | Web Audio API | Last release 2023-09 |
| Synthesis and scheduling | `tone` | | |
| Globe | `cobe` | | |

For vocabulary and review of animations, the `motion` set has skills that go further than this table.
