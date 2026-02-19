import { useEffect, useRef, useId } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
});

export default function MermaidDiagram({ chart }) {
  const ref = useRef(null);
  const id = useId().replace(/:/g, "-");

  useEffect(() => {
    if (!chart || !ref.current) return;

    let cancelled = false;

    (async () => {
      try {
        const { svg, bindFunctions } = await mermaid.render(
          `mermaid-${id}`,
          chart,
        );
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          bindFunctions?.(ref.current);
        }
      } catch (err) {
        console.warn("Mermaid render error:", err);
        if (!cancelled && ref.current) {
          ref.current.textContent = chart;
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  return <div ref={ref} />;
}
