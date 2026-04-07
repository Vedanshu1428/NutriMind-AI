import { useState } from "react";

function FoodLogger({ api, onFoodLogged }) {
  const [formData, setFormData] = useState({
    food_name: "",
    quantity: 1,
    consumed_at: "",
  });
  const [scanData, setScanData] = useState({
    image: null,
    quantity: 1,
    consumed_at: "",
  });
  const [status, setStatus] = useState({ type: "", message: "" });
  const [loading, setLoading] = useState(false);
  const [scanLoading, setScanLoading] = useState(false);

  const handleChange = (event) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleScanChange = (event) => {
    const { name, value, files } = event.target;
    setScanData((current) => ({
      ...current,
      [name]: files ? files[0] : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const payload = {
        food_name: formData.food_name,
        quantity: Number(formData.quantity),
        consumed_at: formData.consumed_at ? new Date(formData.consumed_at).toISOString() : undefined,
      };

      await api.post("/log-food", payload);
      setStatus({ type: "success", message: "Meal logged successfully." });
      setFormData({ food_name: "", quantity: 1, consumed_at: "" });
      onFoodLogged();
    } catch (requestError) {
      setStatus({
        type: "error",
        message: requestError.response?.data?.detail || "Unable to log food. Use a food from the seeded dataset.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleScanSubmit = async (event) => {
    event.preventDefault();
    setScanLoading(true);
    setStatus({ type: "", message: "" });

    try {
      const payload = new FormData();
      payload.append("image", scanData.image);
      payload.append("quantity", String(Number(scanData.quantity)));
      if (scanData.consumed_at) {
        payload.append("consumed_at", new Date(scanData.consumed_at).toISOString());
      }

      const response = await api.post("/scan-food", payload, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setStatus({
        type: "success",
        message: `Detected ${response.data.matched_food} (${response.data.confidence} confidence) and auto-logged ${response.data.estimated_calories} calories.`,
      });
      setScanData({ image: null, quantity: 1, consumed_at: "" });
      event.target.reset();
      onFoodLogged();
    } catch (requestError) {
      setStatus({
        type: "error",
        message: requestError.response?.data?.detail || "Unable to scan and log this food image.",
      });
    } finally {
      setScanLoading(false);
    }
  };

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Food logging</p>
          <h2>Track what you eat</h2>
        </div>
      </div>

      <form className="food-form" onSubmit={handleSubmit}>
        <label>
          Food name
          <input
            type="text"
            name="food_name"
            placeholder="Pizza, Salad, Soda..."
            value={formData.food_name}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          Quantity
          <input type="number" step="0.5" min="0.5" name="quantity" value={formData.quantity} onChange={handleChange} required />
        </label>
        <label>
          Time
          <input type="datetime-local" name="consumed_at" value={formData.consumed_at} onChange={handleChange} />
        </label>
        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? "Saving..." : "Log Meal"}
        </button>
      </form>

      <form className="food-form scan-form" onSubmit={handleScanSubmit}>
        <label className="file-picker">
          Food image
          <input type="file" name="image" accept="image/*" onChange={handleScanChange} required />
        </label>
        <label>
          Estimated quantity
          <input type="number" step="0.5" min="0.5" name="quantity" value={scanData.quantity} onChange={handleScanChange} required />
        </label>
        <label>
          Time
          <input type="datetime-local" name="consumed_at" value={scanData.consumed_at} onChange={handleScanChange} />
        </label>
        <button type="submit" className="secondary-btn" disabled={scanLoading || !scanData.image}>
          {scanLoading ? "Scanning..." : "Scan Food Image"}
        </button>
      </form>

      <div className="hint-box">
        <strong>Supported foods:</strong> Pizza, Burger, Soda, French Fries, Ice Cream, Salad, Oatmeal, Grilled Chicken,
        Egg Omelette, Fruit Smoothie, Brown Rice Bowl, Greek Yogurt. Image scan maps uploaded meals to the closest item in this set.
      </div>

      {status.message ? (
        <p className={status.type === "error" ? "error-text" : "success-text"}>{status.message}</p>
      ) : null}
    </section>
  );
}

export default FoodLogger;
