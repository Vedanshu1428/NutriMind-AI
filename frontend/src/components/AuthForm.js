import { useState } from "react";

const initialSignupState = {
  email: "",
  password: "",
  age: "",
  weight: "",
  height: "",
  goal: "weight_loss",
  diet_preference: "balanced",
  city: "",
  country: "India",
  notification_opt_in: false,
};

function AuthForm({ onAuthenticated, api }) {
  const [mode, setMode] = useState("login");
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [signupData, setSignupData] = useState(initialSignupState);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLoginChange = (event) => {
    setLoginData({ ...loginData, [event.target.name]: event.target.value });
  };

  const handleSignupChange = (event) => {
    const value = event.target.type === "checkbox" ? event.target.checked : event.target.value;
    setSignupData({ ...signupData, [event.target.name]: value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/login" : "/signup";
      const payload =
        mode === "login"
          ? loginData
          : {
              ...signupData,
              age: Number(signupData.age),
              weight: Number(signupData.weight),
              height: Number(signupData.height),
              city: signupData.city || undefined,
              country: signupData.country || undefined,
            };

      const response = await api.post(endpoint, payload);
      localStorage.setItem("smart_nutrition_token", response.data.access_token);
      localStorage.setItem("smart_nutrition_user", JSON.stringify(response.data.user));
      onAuthenticated(response.data.user);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const formData = mode === "login" ? loginData : signupData;
  const onChange = mode === "login" ? handleLoginChange : handleSignupChange;

  return (
    <section className="panel auth-panel">
      <div className="auth-header">
        <div>
          <p className="eyebrow">Smart Nutrition Coach</p>
          <h1>Your nutrition guidance, built around daily habits.</h1>
        </div>
        <div className="mode-switch">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "signup" ? "active" : ""}
            onClick={() => setMode("signup")}
          >
            Signup
          </button>
        </div>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input type="email" name="email" value={formData.email} onChange={onChange} required />
        </label>

        <label>
          Password
          <input type="password" name="password" value={formData.password} onChange={onChange} required />
        </label>

        {mode === "signup" && (
          <>
            <label>
              Age
              <input type="number" name="age" value={signupData.age} onChange={onChange} required />
            </label>
            <label>
              Weight (kg)
              <input type="number" step="0.1" name="weight" value={signupData.weight} onChange={onChange} required />
            </label>
            <label>
              Height (cm)
              <input type="number" step="0.1" name="height" value={signupData.height} onChange={onChange} required />
            </label>
            <label>
              Goal
              <select name="goal" value={signupData.goal} onChange={onChange}>
                <option value="weight_loss">Lose weight</option>
                <option value="maintain">Maintain weight</option>
                <option value="weight_gain">Gain weight</option>
              </select>
            </label>
            <label>
              Diet Preference
              <select name="diet_preference" value={signupData.diet_preference} onChange={onChange}>
                <option value="balanced">Balanced</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="high_protein">High Protein</option>
                <option value="low_carb">Low Carb</option>
              </select>
            </label>
            <label>
              City
              <input type="text" name="city" value={signupData.city} onChange={onChange} placeholder="Bengaluru" />
            </label>
            <label>
              Country
              <input type="text" name="country" value={signupData.country} onChange={onChange} />
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                name="notification_opt_in"
                checked={signupData.notification_opt_in}
                onChange={onChange}
              />
              Enable habit nudges
            </label>
          </>
        )}

        {error ? <p className="error-text">{error}</p> : null}

        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
        </button>
      </form>
    </section>
  );
}

export default AuthForm;
