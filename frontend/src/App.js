import { useEffect, useRef, useState } from "react";
import api from "./api";
import AuthForm from "./components/AuthForm";
import Dashboard from "./components/Dashboard";
import FoodLogger from "./components/FoodLogger";

const initialRecommendations = { suggestions: [], nudges: [], habit_insights: [], health_score: 0 };
const initialDietPlan = { week_start: "", calorie_target: 0, focus: "", generated_at: "", days: [] };
const initialRestaurants = { resolved_location: "", suggestions: [], cached: false };
const initialAnalytics = {
  range_start: "",
  range_end: "",
  avg_calories: 0,
  avg_protein: 0,
  avg_health_score: 0,
  consistency_score: 0,
  streak_days: 0,
  calorie_goal: 0,
  daily_trends: [],
};
const initialNotifications = { enabled: false, notifications: [] };
const initialSummary = {
  total_calories: 0,
  total_protein: 0,
  total_carbs: 0,
  total_fats: 0,
  calorie_goal: 0,
  remaining_calories: 0,
  logs: [],
  habit_insights: [],
  health_score: 0,
};

function App() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("smart_nutrition_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [summary, setSummary] = useState(initialSummary);
  const [recommendations, setRecommendations] = useState(initialRecommendations);
  const [dietPlan, setDietPlan] = useState(initialDietPlan);
  const [restaurants, setRestaurants] = useState(initialRestaurants);
  const [analytics, setAnalytics] = useState(initialAnalytics);
  const [notificationFeed, setNotificationFeed] = useState(initialNotifications);
  const [aiAdvice, setAiAdvice] = useState("");
  const [loadingAI, setLoadingAI] = useState(false);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState("");
  const [preferencesLoading, setPreferencesLoading] = useState(false);
  const deliveredNotifications = useRef(new Set());

  const logout = () => {
    localStorage.removeItem("smart_nutrition_token");
    localStorage.removeItem("smart_nutrition_user");
    setUser(null);
    setSummary(initialSummary);
    setRecommendations(initialRecommendations);
    setDietPlan(initialDietPlan);
    setRestaurants(initialRestaurants);
    setAnalytics(initialAnalytics);
    setNotificationFeed(initialNotifications);
    setAiAdvice("");
  };

  const fetchRestaurants = async (profile = user) => {
    const params = {};
    if (profile?.latitude != null) {
      params.latitude = profile.latitude;
    }
    if (profile?.longitude != null) {
      params.longitude = profile.longitude;
    }
    if (profile?.city) {
      params.city = profile.city;
    }
    if (profile?.country) {
      params.country = profile.country;
    }
    const response = await api.get("/restaurants/suggestions", { params });
    setRestaurants(response.data);
  };

  const fetchNotificationFeed = async () => {
    const response = await api.get("/notifications/feed");
    setNotificationFeed(response.data);
    return response.data;
  };

  const fetchDashboardData = async () => {
    setLoadingDashboard(true);
    setDashboardError("");
    try {
      const [summaryResponse, recommendationResponse, dietPlanResponse, analyticsResponse, notificationResponse] = await Promise.all([
        api.get("/daily-summary"),
        api.get("/recommendations"),
        api.get("/weekly-diet-plan"),
        api.get("/analytics/weekly-trends"),
        fetchNotificationFeed(),
      ]);
      setSummary(summaryResponse.data);
      setRecommendations(recommendationResponse.data);
      setDietPlan(dietPlanResponse.data);
      setAnalytics(analyticsResponse.data);
      setNotificationFeed(notificationResponse);
      await fetchRestaurants();
    } catch (requestError) {
      setDashboardError(requestError.response?.data?.detail || "Unable to load dashboard data.");
    } finally {
      setLoadingDashboard(false);
    }
  };

  const fetchAIAdvice = async () => {
    setLoadingAI(true);
    try {
      const response = await api.post("/ai-recommend", {
        daily_food_log: summary.logs,
      });
      setAiAdvice(response.data.advice);
    } catch (requestError) {
      setAiAdvice(requestError.response?.data?.detail || "Unable to load AI advice.");
    } finally {
      setLoadingAI(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user]);

  useEffect(() => {
    if (!user?.notification_opt_in) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      fetchNotificationFeed().catch(() => {});
    }, 60000);

    return () => window.clearInterval(intervalId);
  }, [user?.notification_opt_in]);

  useEffect(() => {
    if (typeof window === "undefined" || !("Notification" in window) || Notification.permission !== "granted") {
      return;
    }

    const dueNotifications = notificationFeed.notifications.filter(
      (item) => !item.is_read && new Date(item.scheduled_for).getTime() <= Date.now(),
    );

    dueNotifications.forEach((item) => {
      if (deliveredNotifications.current.has(item.id)) {
        return;
      }

      deliveredNotifications.current.add(item.id);
      const notification = new Notification(item.title, { body: item.message });
      notification.onclick = () => window.focus();
      api.post(`/notifications/${item.id}/read`).catch(() => {});
    });
  }, [notificationFeed.notifications]);

  const updatePreferences = async (payload) => {
    setPreferencesLoading(true);
    try {
      const response = await api.patch("/profile/preferences", payload);
      setUser(response.data);
      localStorage.setItem("smart_nutrition_user", JSON.stringify(response.data));
      return response.data;
    } finally {
      setPreferencesLoading(false);
    }
  };

  const handleEnableNotifications = async () => {
    if (!("Notification" in window)) {
      setDashboardError("This browser does not support notifications.");
      return;
    }

    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      setDashboardError("Notification permission was not granted.");
      return;
    }

    const updatedUser = await updatePreferences({ notification_opt_in: true });
    setDashboardError("");
    fetchNotificationFeed();
    setUser(updatedUser);
  };

  const handleLocationCapture = async () => {
    if (!navigator.geolocation) {
      setDashboardError("Geolocation is not supported in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const updatedUser = await updatePreferences({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setDashboardError("");
        fetchRestaurants(updatedUser).catch(() => {});
      },
      () => {
        setDashboardError("Location access was denied, so local restaurant suggestions are still using your saved profile.");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  if (!user) {
    return (
      <main className="app-shell auth-shell">
        <AuthForm api={api} onAuthenticated={setUser} />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Smart Nutrition Coach</p>
          <h1>Make healthier food decisions with data and habit-aware coaching.</h1>
        </div>
        <button type="button" className="secondary-btn" onClick={logout}>
          Logout
        </button>
      </header>

      <FoodLogger api={api} onFoodLogged={fetchDashboardData} />

      {dashboardError ? <p className="error-text">{dashboardError}</p> : null}
      {loadingDashboard ? (
        <section className="panel">
          <p className="empty-state">Loading your dashboard...</p>
        </section>
      ) : (
        <Dashboard
          user={user}
          summary={summary}
          recommendations={recommendations}
          dietPlan={dietPlan}
          restaurants={restaurants}
          analytics={analytics}
          notificationFeed={notificationFeed}
          aiAdvice={aiAdvice}
          onRefreshAI={fetchAIAdvice}
          onEnableNotifications={handleEnableNotifications}
          onUseLocation={handleLocationCapture}
          preferencesLoading={preferencesLoading}
          loadingAI={loadingAI}
        />
      )}
    </main>
  );
}

export default App;
