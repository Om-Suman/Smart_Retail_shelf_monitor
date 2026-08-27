import { Boxes } from "lucide-react";

export default function InventorySummary({ products }) {
  return (
    <article className="panel">
      <div className="panel-heading">
        <Boxes size={18} />
        <h3>Inventory Summary</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Quantity</th>
            </tr>
          </thead>
          <tbody>
            {products.map((item) => (
              <tr key={item.product_name}>
                <td>{item.product_name}</td>
                <td>{item.quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
