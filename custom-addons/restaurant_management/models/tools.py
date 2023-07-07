from calendar import monthrange
from datetime import date


def compute_date_start_end(report_year, report_month):
    year=int(report_year)
    month=int(report_month)
    date_start = date(year=year, month=month, day=1)
    date_end = date(year=year, month=month, day=monthrange(year, month)[1])

    return date_start, date_end


def compute_restaurant_ratings(faults_per_restaurant, audits_per_restaurant):
    """Create the array of dicts representing restaurant rating

    Args:
        faults_per_restaurant (list[tuple[int, str, int]]): Faults per restaurant
        audits_per_restaurant (list[tuple[int, int]]): Audits per restaurant

    Returns:
        list[dict[str, Any]]: Restaurant rating
    """
    restaurant_to_audit_count = {r[0]: r[1] for r in audits_per_restaurant}
    results = []
    for restaurant_id, restaurant_name, fault_count in faults_per_restaurant:
        results.append({
            "restaurant_id": restaurant_id,
            "restaurant_name": restaurant_name,
            "fault_count": fault_count,
            "fault_count_per_audit": round(fault_count/restaurant_to_audit_count.get(restaurant_id, 1), 2)
        })
    
    response = []
    rating = 0
    for row in sorted(results, key=lambda r: r["fault_count_per_audit"]):
        if response and response[-1]["fault_count_per_audit"] == row["fault_count_per_audit"]:
            response[-1]["restaurant_ids"].append(row["restaurant_id"])
            response[-1]["restaurant_names"].append(row["restaurant_name"])
            response[-1]["fault_count"].append(row["fault_count"])
        elif not response or response[-1]["fault_count_per_audit"] != row["fault_count_per_audit"]:
            rating += 1
            response.append({
                "rating": rating,
                "fault_count_per_audit": row["fault_count_per_audit"],
                "restaurant_ids": [row["restaurant_id"]],
                "restaurant_names": [row["restaurant_name"]],
                "fault_count": [row["fault_count"]]
            })

    return response