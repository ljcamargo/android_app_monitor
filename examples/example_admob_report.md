# AdMob Performance Report: `com.example.app`
**Reporting Period:** 2026-08-05 to 2026-08-11

> **Note:** This is a sanitized example report. App names, publisher IDs, ad unit IDs,
> and figures are fictionalized but structurally faithful to a real run.

---

### 1. Overall Monetization Summary
The app generated **$2.55** over the 7-day period. Performance was driven by a high volume of banner requests, but monetization efficiency was heavily impacted by low fill rates and low-value impressions.

*   **Total Earnings:** $2.55
*   **Impressions:** 5,153
*   **Clicks:** 62
*   **CTR:** 1.20%
*   **Match Rate:** 49.72%
*   **eCPM:** $0.50

---

### 2. Day-to-Day Variations
*   **Volume Spike (2026-08-06):** Ad requests peaked at 3,911 (mostly Banner traffic). Despite the high volume, the match rate dropped to roughly 42%, suggesting potential inventory exhaustion or low bidder demand during this spike.
*   **Earnings Peak (2026-08-11):** Despite the lowest request volume of the week, this day saw the highest earnings ($0.48). This was driven by a significant jump in Banner eCPM ($0.51) and Interstitial eCPM ($3.96), indicating that quality traffic is currently more valuable to advertisers than raw volume.

---

### 3. Per-Ad-Unit Comparison

| Ad Unit | Earnings | CTR | eCPM | Performance Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Banner** | $1.64 | 0.36% | $0.35 | **High volume/Low value.** Drives most revenue but has a poor match rate (~45%). |
| **App Open** | $0.64 | 12.46% | $2.27 | **High efficiency.** Excellent CTR and strong eCPM. |
| **Interstitial**| $0.27 | 7.30% | $1.99 | **High potential.** High eCPM, but extremely low impression volume. |
| **Native** | $0.00 | 0.00% | $0.00 | **Inactive.** No requests sent. |

*   **Underperformers:** The **Banner** unit suffers from a very low eCPM and match rate. The **Native** unit is currently non-functional.
*   **Top Performers:** The **App Open** unit is the most efficient revenue driver relative to request volume.

---

### 4. Actionable Recommendations

1.  **Optimize Banner Match Rate:** A ~45% match rate for banners is suboptimal. Ensure you are using **Google Optimized Mediation** or adding additional ad networks via Bidding to fill the ~55% of unfilled requests.
2.  **Enable Native Ads:** The Native ad unit shows zero activity. If the app UI supports it, integrate Native ads, as they often provide higher engagement and eCPM than standard banners.
3.  **Increase Interstitial Frequency:** The Interstitial eCPM is strong ($1.99), but the ratio of impressions to requests is very low. If user experience allows, trigger Interstitials during natural transition points (e.g., screen changes or task completion) to increase total impressions.
4.  **Review Banner Placement:** The current Banner CTR is quite low (0.36%). Consider experimenting with "Adaptive Banners" to ensure the ad size is perfectly optimized for the device screen, which can improve both viewability and CTR.
5.  **Traffic Quality Analysis:** Investigate why request volume fluctuated so significantly (e.g., 3,911 on Aug 6 vs 2,293 on Aug 11). If this is due to user behavior, focus acquisition efforts on the days/sources that generate the high-eCPM traffic seen on Aug 11.
