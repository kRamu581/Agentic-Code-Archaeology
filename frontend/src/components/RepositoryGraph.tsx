import { useEffect, useMemo, useRef } from "react";
import type { ComponentProps } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { getRepositoryNodeLabel, normalizeRepositoryGraph } from "./repositoryGraphData";
import type { GraphLink, GraphNode, RepositoryGraphData } from "./repositoryGraphData";

function hasCoordinates(value: unknown): value is { x: number; y: number } {
  return typeof value === "object" && value !== null &&
    "x" in value && typeof value.x === "number" &&
    "y" in value && typeof value.y === "number";
}

function getEndpointPosition(endpoint: unknown, nodes: GraphNode[]) {
  if (hasCoordinates(endpoint)) return endpoint;

  const id = typeof endpoint === "string"
    ? endpoint
    : typeof endpoint === "object" && endpoint !== null && "id" in endpoint && typeof endpoint.id === "string"
      ? endpoint.id
      : undefined;
  const node = id ? nodes.find((candidate) => candidate.id === id) : undefined;
  return hasCoordinates(node) ? node : undefined;
}

interface GraphProps {
  graphData: RepositoryGraphData;
}

function RepositoryGraph({ graphData }: GraphProps) {
  type ForceGraphHandle = NonNullable<ComponentProps<typeof ForceGraph2D<GraphNode, GraphLink>>["ref"]>["current"];
  const graphRef = useRef<ForceGraphHandle>(undefined);
  const hasZoomedToFit = useRef(false);
  const data = useMemo(() => normalizeRepositoryGraph(graphData), [graphData]);

  useEffect(() => {
    hasZoomedToFit.current = false;
  }, [data]);

  if (data.nodes.length === 0) {
    return <p className="graph-empty-state">No repository relationship data is available yet.</p>;
  }

  return (
    <>
      <ul className="graph-legend" aria-label="Graph legend">
        <li><span className="graph-legend-swatch graph-legend-commit" />Commit</li>
        <li><span className="graph-legend-swatch graph-legend-file" />File</li>
        <li><span className="graph-legend-link" />Changed together</li>
      </ul>
      <div className="repository-graph-canvas">
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          nodeLabel={getRepositoryNodeLabel}
          nodeColor={(node) => node.type === "commit" ? "#f59e0b" : "#3b82f6"}
          nodeVal={(node) => node.type === "commit" ? 6 : 2}
          nodeRelSize={8}
          linkColor={() => "#6b7280"}
          linkWidth={1.5}
          linkVisibility={() => true}
          linkCanvasObjectMode="before"
          linkCanvasObject={(link, context, globalScale) => {
            const source = getEndpointPosition(link.source, data.nodes);
            const target = getEndpointPosition(link.target, data.nodes);
            if (!source || !target) return;

            context.save();
            context.beginPath();
            context.moveTo(source.x, source.y);
            context.lineTo(target.x, target.y);
            context.strokeStyle = "#6b7280";
            context.lineWidth = 1.5 / globalScale;
            context.stroke();
            context.restore();
          }}
          linkDirectionalParticles={1}
          linkDirectionalParticleColor={() => "#d1d5db"}
          onEngineStop={() => {
            if (!hasZoomedToFit.current) {
              hasZoomedToFit.current = true;
              graphRef.current?.zoomToFit(400, 40);
            }
          }}
        />
      </div>
    </>
  );
}

export default RepositoryGraph;
