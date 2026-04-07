function TrendChart({ data, calorieGoal }) {
  const maxCalories = Math.max(calorieGoal || 0, ...data.map((point) => point.calories), 1);

  return (
    <div className="trend-chart">
      {data.map((point) => {
        const height = `${Math.max(8, (point.calories / maxCalories) * 100)}%`;
        return (
          <div className="trend-bar-group" key={point.date}>
            <div className="trend-bar-shell">
              <div className="trend-bar" style={{ height }} title={`${point.calories} calories`} />
            </div>
            <strong>{new Date(point.date).toLocaleDateString(undefined, { weekday: "short" })}</strong>
            <small>{point.health_score}/100</small>
          </div>
        );
      })}
    </div>
  );
}

function Dashboard({
  user,
  summary,
  recommendations,
  dietPlan,
  restaurants,
  analytics,
  notificationFeed,
  aiAdvice,
  onRefreshAI,
  onEnableNotifications,
  onUseLocation,
  preferencesLoading,
  loadingAI,
}) {
  const healthScore = recommendations.health_score || summary.health_score;

  return (
    <section className="dashboard-grid">
      <article className="panel hero-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Daily overview</p>
            <h2>Welcome back, {user.email}</h2>
          </div>
          <span className="goal-chip">{user.goal.replaceAll("_", " ")}</span>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <span>Calories</span>
            <strong>{summary.total_calories}</strong>
            <small>Goal: {summary.calorie_goal}</small>
          </div>
          <div className="stat-card">
            <span>Protein</span>
            <strong>{summary.total_protein} g</strong>
            <small>Support muscle and satiety</small>
          </div>
          <div className="stat-card">
            <span>Weekly streak</span>
            <strong>{analytics.streak_days} days</strong>
            <small>Consistency compounds over time</small>
          </div>
          <div className="stat-card">
            <span>Avg health score</span>
            <strong>{analytics.avg_health_score || healthScore}/100</strong>
            <small>Based on meal quality and goal fit</small>
          </div>
          <div className="stat-card">
            <span>Consistency score</span>
            <strong>{analytics.consistency_score}/100</strong>
            <small>Logging plus calorie-goal adherence</small>
          </div>
        </div>

        <div className="progress-note">
          <span>Remaining calories</span>
          <strong>{summary.remaining_calories}</strong>
        </div>
      </article>

      <article className="panel analytics-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Weekly trends</p>
            <h2>Analytics dashboard</h2>
          </div>
          <span className="goal-chip">
            {analytics.range_start} to {analytics.range_end}
          </span>
        </div>
        <div className="stats-grid compact-stats">
          <div className="stat-card">
            <span>Avg calories</span>
            <strong>{analytics.avg_calories}</strong>
            <small>Goal: {analytics.calorie_goal}</small>
          </div>
          <div className="stat-card">
            <span>Avg protein</span>
            <strong>{analytics.avg_protein} g</strong>
            <small>Weekly mean intake</small>
          </div>
        </div>
        <TrendChart data={analytics.daily_trends} calorieGoal={analytics.calorie_goal} />
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Recommendations</p>
            <h2>Contextual coaching</h2>
          </div>
        </div>
        <ul className="card-list">
          {recommendations.suggestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Nudges</p>
            <h2>Push-ready habit queue</h2>
          </div>
          <button type="button" className="secondary-btn" onClick={onEnableNotifications} disabled={preferencesLoading}>
            {notificationFeed.enabled ? "Notifications On" : preferencesLoading ? "Saving..." : "Enable Notifications"}
          </button>
        </div>
        <ul className="card-list accent-list">
          {notificationFeed.notifications.length ? (
            notificationFeed.notifications.map((item) => (
              <li key={item.id}>
                <strong>{item.title}:</strong> {item.message}
              </li>
            ))
          ) : (
            <li>No nudges scheduled yet. Turn notifications on to queue habit reminders.</li>
          )}
        </ul>
      </article>

      <article className="panel diet-plan-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Weekly plan</p>
            <h2>Personalized diet plan</h2>
          </div>
          <span className="goal-chip">{dietPlan.focus || user.diet_preference.replaceAll("_", " ")}</span>
        </div>
        <div className="plan-grid">
          {dietPlan.days.map((dayPlan) => (
            <div className="plan-card" key={dayPlan.day}>
              <h3>{dayPlan.day}</h3>
              <p>{dayPlan.note}</p>
              <ul>
                <li>Breakfast: {dayPlan.breakfast.name}</li>
                <li>Lunch: {dayPlan.lunch.name}</li>
                <li>Dinner: {dayPlan.dinner.name}</li>
                <li>Snack: {dayPlan.snack.name}</li>
              </ul>
              <small>{dayPlan.daily_target_calories} calories target</small>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Nearby picks</p>
            <h2>Healthy restaurants</h2>
          </div>
          <button type="button" className="secondary-btn" onClick={onUseLocation} disabled={preferencesLoading}>
            {preferencesLoading ? "Updating..." : "Use My Location"}
          </button>
        </div>
        <p className="hint-box">Suggestions centered on {restaurants.resolved_location || "your saved area"}.</p>
        <div className="restaurant-list">
          {restaurants.suggestions.map((restaurant) => (
            <div className="restaurant-card" key={restaurant.name}>
              <h3>{restaurant.name}</h3>
              <p>{restaurant.address}</p>
              <strong>{restaurant.distance_km} km away</strong>
              <p>{restaurant.why_it_matches}</p>
              <small>{restaurant.top_picks.join(" • ")}</small>
            </div>
          ))}
        </div>
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Habit insights</p>
            <h2>Recent patterns</h2>
          </div>
        </div>
        <ul className="card-list">
          {recommendations.habit_insights.length ? (
            recommendations.habit_insights.map((item) => <li key={item}>{item}</li>)
          ) : (
            <li>Your recent meals are still building a pattern. Log a few more days to unlock stronger trend insights.</li>
          )}
        </ul>
      </article>

      <article className="panel ai-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">AI coach</p>
            <h2>Personalized advice</h2>
          </div>
          <button type="button" className="secondary-btn" onClick={onRefreshAI} disabled={loadingAI}>
            {loadingAI ? "Thinking..." : "Refresh AI Advice"}
          </button>
        </div>
        <p className="ai-copy">{aiAdvice || "Request AI advice to get a personalized nutrition summary."}</p>
      </article>

      <article className="panel logs-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Meal history</p>
            <h2>Today's food logs</h2>
          </div>
        </div>
        {summary.logs.length ? (
          <div className="log-table">
            <div className="log-table-row log-table-header">
              <span>Food</span>
              <span>Qty</span>
              <span>Calories</span>
              <span>Time</span>
            </div>
            {summary.logs.map((log) => (
              <div className="log-table-row" key={log.id}>
                <span>{log.food_name}</span>
                <span>{log.quantity}</span>
                <span>{log.total_calories}</span>
                <span>{new Date(log.consumed_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-state">No meals logged yet for today.</p>
        )}
      </article>
    </section>
  );
}

export default Dashboard;
