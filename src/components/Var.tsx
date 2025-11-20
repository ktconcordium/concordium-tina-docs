import variables from "@/content/variables.json";

type VarProps = {
  name: string;
  children?: React.ReactNode;
};

export function Var({ name, children }: VarProps) {
  const text = (variables as Record<string, string>)[name] ?? name;

  // If children provided, prefer them (e.g. custom label)
  return <>{children ?? text}</>;
}