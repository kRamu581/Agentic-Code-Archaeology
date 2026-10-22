export interface GraphNode {
  id: string;
  label: string;
  type: string;
  message?: string;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
}

export interface RepositoryGraphData {
  nodes: GraphNode[];
  edges: GraphLink[];
}

export function getRepositoryNodeLabel(node: GraphNode) {
  return node.type === "commit"
    ? `${node.label.slice(0, 7)}${node.message ? ` - ${node.message}` : ""}`
    : node.label;
}

export function normalizeRepositoryGraph(graphData: RepositoryGraphData) {
  const nodesByFilePath = new Map<string, GraphNode>();
  const nodeIds = new Map<string, string>();
  const nodes: GraphNode[] = [];

  graphData.nodes.forEach((node) => {
    if (node.type !== "file") {
      nodes.push(node);
      nodeIds.set(node.id, node.id);
      return;
    }

    const existing = nodesByFilePath.get(node.label);
    if (existing) {
      nodeIds.set(node.id, existing.id);
      return;
    }

    nodesByFilePath.set(node.label, node);
    nodeIds.set(node.id, node.id);
    nodes.push(node);
  });

  const linksByKey = new Map<string, GraphLink>();
  graphData.edges.forEach((edge) => {
    const sourceId = typeof edge.source === "string" ? edge.source : edge.source.id;
    const targetId = typeof edge.target === "string" ? edge.target : edge.target.id;
    const source = nodeIds.get(sourceId);
    const target = nodeIds.get(targetId);
    if (!source || !target || source === target) return;
    linksByKey.set(`${source}\0${target}`, { source, target });
  });

  return { nodes, links: [...linksByKey.values()] };
}
