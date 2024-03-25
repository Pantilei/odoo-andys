
# Department queries
fault_count_by_department_query = """
WITH fault_count_per_check_list_category as (
    select 
        check_list_category_id, 
        sum(fault_count) as faults_count
    from restaurant_management_fault_registry 
    where 
        state = 'confirm' and
        fault_date >= %s and
        fault_date <= %s and
        restaurant_id IN %s and
        check_list_category_id IN %s
    group by check_list_category_id
)

SELECT 
    fcpclc.check_list_category_id,
    fcpclc.faults_count,
    rmclc.name as check_list_category_name
FROM fault_count_per_check_list_category as fcpclc
LEFT JOIN restaurant_management_check_list_category as rmclc
ON fcpclc.check_list_category_id = rmclc.id;
"""

relative_by_month_fault_count_query = """
select 
    faults_by_month_table.faults_count - lag(faults_by_month_table.faults_count) 
    over 
    (order by faults_by_month_table.fault_month) as fault_change
from 
(
    select 
        date_trunc('month', fault_date) as fault_month, 
        sum(fault_count) as faults_count
    from restaurant_management_fault_registry 
    where 
        state = 'confirm' and
        fault_date >= %s and
        fault_date <= %s and 
        check_list_category_id = %s and 
        restaurant_id IN %s
    group by fault_month
) as faults_by_month_table
order by fault_change
limit 1;
"""

restaurant_faults_in_department_query = """
WITH restaurant_to_fault_count AS (
    SELECT 
        restaurant_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and 
        check_list_category_id = %s and 
        restaurant_id IN %s
    GROUP BY restaurant_id
)
select 
    rmr.id as restaurant_id,
    rmr.name as restaurant_name,
    COALESCE(restaurant_to_fault_count.total_faults, 0) as total_faults
from restaurant_to_fault_count 
right join restaurant_management_restaurant rmr
on restaurant_to_fault_count.restaurant_id = rmr.id
where rmr.id IN %s
"""

restaurant_audit_count_query = """
select 
    restaurant_id,
    sum(1) as audit_count
from restaurant_management_restaurant_audit
where
    state = 'confirm' and
    audit_date >= %s and
    audit_date <= %s and
    restaurant_id IN %s
group by restaurant_id
"""

top_violations_by_department_query = """
select 
    check_list_fault_count.check_list_id as id, 
    rmcl.name as name,
    COALESCE(check_list_fault_count.total_faults, 0) as total_faults
from (
    SELECT 
        check_list_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and 
        check_list_category_id = %s and 
        restaurant_id IN %s
    GROUP BY check_list_id 
) as check_list_fault_count

inner join restaurant_management_check_list rmcl 
on check_list_fault_count.check_list_id = rmcl.id
order by total_faults desc
limit 10;
"""

faults_by_months_in_department_query = """
SELECT 
    EXTRACT(MONTH FROM faults_by_date.fault_month) AS month_of_faults, 
    faults_by_date.total_faults AS total_faults
FROM
(
    SELECT 
        DATE_TRUNC('month', rmfr.fault_date) AS fault_month,
        SUM(rmfr.fault_count) AS total_faults
    FROM restaurant_management_fault_registry rmfr 
    WHERE 
        rmfr.state = 'confirm' AND 
        rmfr.fault_date >= %s AND 
        rmfr.fault_date <= %s AND
        rmfr.check_list_category_id = %s AND
        rmfr.restaurant_id IN %s
    GROUP BY fault_month
    ORDER BY fault_month DESC
) AS faults_by_date;
"""

department_rating_query = """
SELECT 
    ARRAY_AGG(department_faults.id) AS department_ids,
    ARRAY_AGG(department_faults.name) AS department_names, 
    fault_count
FROM (
    SELECT 
        rmclc.id,
        rmclc.name,
        COALESCE(department_fault_counts.total_faults, 0) as fault_count
    FROM 
        restaurant_management_check_list_category rmclc 
    LEFT JOIN
    (
        SELECT 
            check_list_category_id,
            SUM(fault_count) AS total_faults 
            FROM restaurant_management_fault_registry 
        WHERE
            state = 'confirm' AND 
            fault_date >= %s AND 
            fault_date <= %s AND
            restaurant_id IN %s
        GROUP BY check_list_category_id 
    ) AS department_fault_counts
    ON department_fault_counts.check_list_category_id = rmclc.id
    WHERE 
        rmclc.active = true AND 
        rmclc.no_fault_category = false AND 
        rmclc.default_category = true
) AS department_faults
GROUP BY fault_count
ORDER BY fault_count ASC; 
"""


# Company queries
planned_audit_count_by_year = """
select 
	year,
	sum(jan) as jan,
	sum(feb) as feb,
	sum(mar) as mar,
	sum(apr) as apr,
	sum(may) as may,
	sum(jun) as jun,
	sum(jul) as jul,
	sum(aug) as aug,
	sum(sept) as sept,
	sum(oct) as oct,
	sum(nov) as nov,
	sum("dec") as dec
from restaurant_management_planned_audits rmpa 
where 
	restaurant_id in %s and 
	year = %s
group by year
"""

actual_audit_count_by_year = """
select 
	extract(month from date_trunc('month', audit_date)) as audit_month,
	sum(1) as audit_count
from restaurant_management_restaurant_audit rmra 
where 
	restaurant_id in %s and 
	audit_date >= %s and 
	audit_date <= %s and 
	state = 'confirm'
group by audit_month
order by audit_month
"""

faults_by_months_in_restaurants_query = """
SELECT 
    EXTRACT(MONTH FROM faults_by_date.fault_month) AS month_of_faults, 
    faults_by_date.total_faults AS total_faults
FROM
(
    SELECT 
        DATE_TRUNC('month', rmfr.fault_date) AS fault_month,
        SUM(rmfr.fault_count) AS total_faults
    FROM restaurant_management_fault_registry rmfr 
    WHERE 
        rmfr.state = 'confirm' AND 
        rmfr.fault_date >= %s AND 
        rmfr.fault_date <= %s AND
        rmfr.restaurant_id IN %s
    GROUP BY fault_month
    ORDER BY fault_month DESC
) AS faults_by_date;
"""

top_faults_by_restaurants_query = """
with check_list_to_fault_count as (
	select
		check_list_id,
		sum(fault_count) as fault_count
	from restaurant_management_fault_registry rmfr 
	where
		state = 'confirm' and
		check_list_id is not null and 
		fault_date >= %s and 
		fault_date <= %s and 
		restaurant_id in %s
	group by check_list_id
	order by fault_count desc 
	limit 10
)

select 
	rmcl.category_id as check_list_category_id,
	rmclc.name as check_list_category_name,
	rmcl.id as id,
	rmcl.name as name,
	cltfc.fault_count as fault_count
from check_list_to_fault_count as cltfc
left join restaurant_management_check_list rmcl on
    cltfc.check_list_id = rmcl.id
left join restaurant_management_check_list_category rmclc on
    rmcl.category_id = rmclc.id
order by fault_count desc 
"""


fault_counts_by_restaurants_query = """
WITH restaurant_to_fault_count AS (
    SELECT 
        restaurant_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and 
        restaurant_id IN %s
    GROUP BY restaurant_id
)
select 
    rmr.id as restaurant_id,
    rmr.name as restaurant_name,
    COALESCE(restaurant_to_fault_count.total_faults, 0) as total_faults
from restaurant_to_fault_count 
right join restaurant_management_restaurant rmr
on restaurant_to_fault_count.restaurant_id = rmr.id
where rmr.id IN %s
"""

# Restaurant queries
faults_by_months_in_restaurants_in_departments_query = """
SELECT 
    EXTRACT(MONTH FROM faults_by_date.fault_month) AS month_of_faults, 
    faults_by_date.total_faults AS total_faults
FROM
(
    SELECT 
        DATE_TRUNC('month', rmfr.fault_date) AS fault_month,
        SUM(rmfr.fault_count) AS total_faults
    FROM restaurant_management_fault_registry rmfr 
    WHERE 
        rmfr.state = 'confirm' AND 
        rmfr.fault_date >= %s AND 
        rmfr.fault_date <= %s AND
        rmfr.restaurant_id IN %s AND
        rmfr.check_list_category_id in %s
    GROUP BY fault_month
    ORDER BY fault_month DESC
) AS faults_by_date;
"""


fault_counts_by_restaurants_in_departments_query = """
WITH restaurant_to_fault_count AS (
    SELECT 
        restaurant_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and 
        restaurant_id IN %s and
        check_list_category_id IN %s
    GROUP BY restaurant_id
)
select 
    rmr.id as restaurant_id,
    rmr.name as restaurant_name,
    COALESCE(restaurant_to_fault_count.total_faults, 0) as total_faults
from restaurant_to_fault_count 
right join restaurant_management_restaurant rmr
on restaurant_to_fault_count.restaurant_id = rmr.id
where rmr.id IN %s
"""

restaurant_rating_within_network_query = """
select 
    rtfc.fault_count,
    array_agg(rtfc.restaurant_id) as restaurants,
    array_agg(rtfc.restaurant_name) as restaurant_names
from (
    select 
        rmr.id as restaurant_id,
        rmr.name as restaurant_name,
        coalesce(restaurant_to_fault_count.restaurant_fault_count, 0) as fault_count
    from (
        select 
            rmfr.restaurant_id as restaurant_id,
            sum(rmfr.fault_count) as restaurant_fault_count
        from restaurant_management_fault_registry as rmfr
        where 
            rmfr.fault_date >= %s and 
            rmfr.fault_date <= %s and 
            rmfr.state = 'confirm'
        group by rmfr.restaurant_id
    ) as restaurant_to_fault_count
    right join restaurant_management_restaurant as rmr
    on rmr.id = restaurant_to_fault_count.restaurant_id
) as rtfc
group by rtfc.fault_count
order by rtfc.fault_count
"""

restaurant_rating_by_audit_type_query = """
select
    rtfc.fault_count as fault_count,
    array_agg(rtfc.restaurant_id) as restaurants,
    array_agg(rtfc.restaurant_name) as restaurant_names

FROM (
    select
        rmr.id AS restaurant_id,
        rmr.name AS restaurant_name,
        COALESCE(restaurant_to_fault_count.restaurant_fault_count, 0) AS fault_count
    FROM (
        select
            rmfr.restaurant_id AS restaurant_id,
            SUM(rmfr.fault_count) AS restaurant_fault_count
        FROM
            restaurant_management_fault_registry AS rmfr
        WHERE
            rmfr.fault_date >= %s
            AND rmfr.fault_date <= %s
            AND rmfr.check_list_type_id = %s
            AND rmfr.state = 'confirm'
        GROUP BY
            rmfr.restaurant_id
    ) AS restaurant_to_fault_count
    RIGHT JOIN restaurant_management_restaurant AS rmr ON rmr.id = restaurant_to_fault_count.restaurant_id
) AS rtfc
GROUP by rtfc.fault_count
order by rtfc.fault_count;
"""

top_violations_in_restaurant_query = """
select 
    check_list_fault_count.check_list_id as id, 
    rmcl.name as name,
    COALESCE(check_list_fault_count.total_faults, 0) as total_faults
from (
    SELECT 
        check_list_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and
        restaurant_id IN %s and
        check_list_category_id IN %s
    GROUP BY check_list_id 
) as check_list_fault_count

inner join restaurant_management_check_list rmcl 
on check_list_fault_count.check_list_id = rmcl.id
order by total_faults desc
limit 10;
"""

# Restaurant network queries
faults_by_months_in_restaurant_network_query = """
WITH faults_by_month AS (
    SELECT 
        DATE_TRUNC('month', rmfr.fault_date) AS fault_month,
        SUM(rmfr.fault_count) AS total_faults
    FROM restaurant_management_fault_registry rmfr 
    WHERE 
        rmfr.state = 'confirm' AND 
        rmfr.fault_date >= %s AND 
        rmfr.fault_date <= %s AND
        rmfr.restaurant_id IN %s
    GROUP BY fault_month
    ORDER BY fault_month DESC
)

SELECT 
    EXTRACT(MONTH FROM fault_month) AS month_of_faults, 
    total_faults
FROM faults_by_month;
"""

audits_by_months_in_restaurant_network_query = """
WITH audits_by_month AS (
    SELECT 
        DATE_TRUNC('month', audit_date) AS audit_month,
        SUM(1) AS total_audits
    FROM restaurant_management_restaurant_audit
    WHERE 
        state = 'confirm' AND 
        audit_date >= %s AND 
        audit_date <= %s AND
        restaurant_id IN %s
    GROUP BY audit_month
    ORDER BY audit_month DESC
)

SELECT 
    EXTRACT(MONTH FROM audit_month) AS audit_month, 
    total_audits
FROM audits_by_month;
"""

yearly_faults_by_check_list_category = """
with check_list_category_to_fault_count as (
    SELECT
    	check_list_category_id,
        SUM(fault_count) as fault_count
    FROM restaurant_management_fault_registry
    WHERE 
        state = 'confirm' AND 
        fault_date >= %s AND 
        fault_date <= %s AND
        restaurant_id IN %s
    GROUP BY check_list_category_id
)

select 
	rmclc.id,
	rmclc.name,
coalesce(clctfc.fault_count, 0) as fault_count
from check_list_category_to_fault_count as clctfc
right join 
	restaurant_management_check_list_category as rmclc 
on clctfc.check_list_category_id = rmclc.id
where
	rmclc.active = true AND
    rmclc.id IN %s
order by fault_count desc
"""

fault_counts_by_restaurants_in_departments_query = """
WITH restaurant_to_fault_count AS (
    SELECT 
        restaurant_id,
        SUM(fault_count) AS total_faults     
    FROM restaurant_management_fault_registry 
    WHERE
        state = 'confirm' and 
        fault_date >= %s and 
        fault_date <= %s and 
        restaurant_id IN %s and
        check_list_category_id IN %s
    GROUP BY restaurant_id
)
select 
    rmr.id as restaurant_id,
    rmr.name as restaurant_name,
    COALESCE(restaurant_to_fault_count.total_faults, 0) as total_faults
from restaurant_to_fault_count 
right join restaurant_management_restaurant rmr
on restaurant_to_fault_count.restaurant_id = rmr.id
where rmr.id IN %s
"""

test_func = """


CREATE OR REPLACE FUNCTION get_restaurant_ratings_by_category(date_from date, date_to date)
returns table (
    category_id INT,
    category_name VARCHAR(255),
    query_result JSONB
) as 
$$

-- Declare variables for the loop
DECLARE 
    category_row RECORD;
    category_result_json JSONB;

begin
	
	DROP TABLE IF EXISTS category_results;
	-- Create a temporary table to store the results
	CREATE TEMPORARY TABLE category_results (
	    category_id INT,
	    category_name VARCHAR(255),
	    query_result JSONB
	);
    -- Fetch all department IDs and names from the "departments" table
    FOR category_row IN SELECT id, name FROM restaurant_management_check_list_category
    LOOP
        select 
            jsonb_agg(rtfc_json.row_data) into category_result_json
        from (
            select json_build_object(
                'fault_count', rtfc_aggr.fault_count,
                'restaurant_ids', rtfc_aggr.restaurants,
                'restaurant_names', rtfc_aggr.restaurant_names
            ) as row_data
            from (
                select
                    rtfc.fault_count as fault_count,
                    array_agg(rtfc.restaurant_id) as restaurants,
                    array_agg(rtfc.restaurant_name) as restaurant_names
                
                FROM (
                    select
                        rmr.id AS restaurant_id,
                        rmr.name AS restaurant_name,
                        COALESCE(restaurant_to_fault_count.restaurant_fault_count, 0) AS fault_count
                    FROM (
                        select
                            rmfr.restaurant_id AS restaurant_id,
                            SUM(rmfr.fault_count) AS restaurant_fault_count
                        FROM
                            restaurant_management_fault_registry AS rmfr
                        WHERE
                            rmfr.fault_date >= date_from
                            AND rmfr.fault_date <= date_to
                            AND rmfr.check_list_category_id = category_row.id
                            AND rmfr.state = 'confirm'
                        GROUP BY
                            rmfr.restaurant_id
                    ) AS restaurant_to_fault_count
                    RIGHT JOIN restaurant_management_restaurant AS rmr ON rmr.id = restaurant_to_fault_count.restaurant_id
                ) AS rtfc
                GROUP by rtfc.fault_count
                order by rtfc.fault_count
            ) as rtfc_aggr
        ) as rtfc_json;
                
        -- Execute the SQL query for the current department and insert the result into the temporary table
        INSERT INTO category_results (category_id, category_name, query_result) values (
            category_row.id, 
            category_row.name,
            category_result_json     
        );
    END LOOP;
   
   return query 
   SELECT category_id, category_name, query_result FROM category_results;
end 
$$ LANGUAGE plpgsql;

select get_restaurant_ratings_by_category('2022-10-01'::date, '2022-10-31'::date);

"""