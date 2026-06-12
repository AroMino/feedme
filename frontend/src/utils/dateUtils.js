export function parseUTC(iso) {
  if (!iso) return new Date(NaN);
  let dateStr = iso;
  const isZoned = dateStr.includes("Z") || dateStr.includes("+") || dateStr.includes("GMT");
  if (!isZoned) {
    dateStr += "Z";
  }
  return new Date(dateStr);
}

export function formatDateShort(iso) {
  const d = parseUTC(iso);
  if (isNaN(d.getTime())) return "Unknown Date";
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC"
  });
}

export function groupArticlesByDate(articles) {
  const groups = {};
  const order = [];
  const now = new Date();
  
  // Use UTC for "Today" and "Yesterday" comparison to match backend/source dates
  const todayUTC = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const yesterdayUTC = new Date(todayUTC);
  yesterdayUTC.setUTCDate(yesterdayUTC.getUTCDate() - 1);

  articles.forEach(article => {
    const pubDate = parseUTC(article.published_at);
    // Extract UTC components for grouping
    const y = pubDate.getUTCFullYear();
    const m = pubDate.getUTCMonth();
    const d = pubDate.getUTCDate();
    const pubDayUTC = new Date(Date.UTC(y, m, d));
    
    let label = "";
    if (pubDayUTC.getTime() === todayUTC.getTime()) {
      label = "Today";
    } else if (pubDayUTC.getTime() === yesterdayUTC.getTime()) {
      label = "Yesterday";
    } else {
      // Format using UTC to avoid local shift
      label = pubDayUTC.toLocaleDateString("en-US", {
        day: "numeric",
        month: "long",
        year: "numeric",
        timeZone: "UTC" // Force UTC formatting
      });
    }

    if (!groups[label]) {
      groups[label] = [];
      order.push(label);
    }
    groups[label].push(article);
  });

  return order.map(label => ({
    label,
    items: groups[label]
  }));
}
