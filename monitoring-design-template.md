# Monitoring Design Template

**Group nr:** 

**Components** (list 3-4 main parts/services of your system):
1. keycloak
2. frontend
3. User db
4. Safety service

---

## Monitoring Strategy

Fill out this table to design your monitoring approach:

| WHAT TO MONITOR | WHY IT MATTERS (user impact) | HOW IT PREVENTS DISASTER |
|-----------------|------------------------------|--------------------------|
| **Example:** API error rate | Users can't complete orders if API is broken | Alert before many customers are affected; can rollback bad deployment |
| 1. Errors | No authentication, performances issues | limit it by scaling or human intervention |
| 2. Latency/Errors/Traffic | latency, User experience | reduce latency, preserve the access to the frontend, logs the errors, organize scaling based on traffic patterns |
| 3. Errors/latency/traffic/saturation | will impact everything, user experience | log errors, faster system reboot |
| 4. Errors/latency | User safety, critical service | logs errors, scale if needed |
| 5. | | |

---

## Failure Scenario Analysis

**Pick one thing or more that could break in your system:**

What could break? User service 

**How would your monitoring detect it?**

health check (liveness probs), 

---

## Guiding Questions

When designing your monitoring, consider:

### The Four Golden Signals
- **Latency:** How long do operations take?
- **Traffic:** How much demand is on your system?
- **Errors:** What's the rate of failed requests?
- **Saturation:** How "full" is your system?

### Black Box vs White Box
- **Black Box:** Can users access your service? (external perspective)
- **White Box:** What's happening inside? (internal metrics)

### Dependencies
- What external services does your system rely on?
- What happens if they fail?
- How would you know?

---

## Tips for Good Monitoring

- **Monitor what users care about** - not just technical metrics  
- **Make alerts actionable** - if you can't do anything, don't alert  
- **Monitor dependencies** - external APIs, etc.
- **Test your monitoring** - make sure alerts actually fire  
- **Think about cascading failures** - one thing breaks, what else fails? Both internal and external dependencies can cause cascades

