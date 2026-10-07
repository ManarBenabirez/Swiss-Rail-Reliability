"""
STEP 3 - ANALYSIS with Spark SQL.   Owner: <name>

Sub-question: Which stations and lines have the most delay, and how does
punctuality change by hour, day and region?

TODO:
  [ ] Define "on time" (e.g. delay < 3 min, like SBB)
  [ ] Worst stations (average delay, % on time, minimum number of arrivals)
  [ ] Worst lines
  [ ] Punctuality by hour of day
  [ ] Punctuality by day of week
  [ ] Punctuality by canton (needs the join)
  [ ] Save each result as CSV in output/ + charts for the report
"""
from spark_session import OUTPUT_DIR, PARQUET_DIR, get_spark


def main():
    spark = get_spark("03_analyze")
    spark.read.parquet(str(PARQUET_DIR / "stops_clean")).createOrReplaceTempView("stops")

    # Example query:
    # spark.sql("""
    #     SELECT station_name, COUNT(*) AS arrivals, AVG(delay_min) AS avg_delay
    #     FROM stops GROUP BY station_name ORDER BY avg_delay DESC LIMIT 20
    # """).show()

    spark.stop()


if __name__ == "__main__":
    main()
