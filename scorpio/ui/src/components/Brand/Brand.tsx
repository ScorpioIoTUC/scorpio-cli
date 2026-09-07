import "./Brand.css";

type BrandProps = { compact?: boolean; inverted?: boolean };

export function Brand({ compact = false, inverted = false }: BrandProps) {
  return (
    <div className={`brand ${inverted ? "brand--inverted" : ""}`}>
      <span className="brand__mark" aria-hidden="true"><span /><span /><span /></span>
      <span className="brand__name">SCORPIO</span>
      {!compact && <span className="brand__suffix">IoT UC</span>}
    </div>
  );
}
