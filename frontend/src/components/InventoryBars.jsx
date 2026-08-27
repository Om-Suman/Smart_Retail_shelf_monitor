export default function InventoryBars({ products }) {
  const maxQuantity = Math.max(...products.map((item) => item.quantity), 1);

  return (
    <div className="bar-list" aria-label="Inventory distribution">
      {products.map((item) => (
        <div className="bar-row" key={item.product_name}>
          <span>{item.product_name}</span>
          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${(item.quantity / maxQuantity) * 100}%` }}
            />
          </div>
          <strong>{item.quantity}</strong>
        </div>
      ))}
    </div>
  );
}
