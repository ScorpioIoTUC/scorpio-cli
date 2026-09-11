import "./Brand.css";

type BrandProps = { compact?: boolean; inverted?: boolean };

export function Brand({ compact = false, inverted = false }: BrandProps) {
  // Render the shared Scorpio brand mark.
  return (
    <div className={`brand ${inverted ? "brand--inverted" : ""}`}>
      <span className="brand__name">SCORPIO</span>
      {!compact && <span className="brand__suffix">IoT UC</span>}
    </div>
  );
}
