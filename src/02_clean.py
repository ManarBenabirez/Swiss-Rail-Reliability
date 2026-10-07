"""
STEP 2 - CLEANING: typed Parquet -> clean Parquet.   Owner: <name>

For each problem: LOOK -> DECIDE (write why) -> APPLY -> COUNT rows before/after.

TODO:
  [ ] Missing values (e.g. no actual arrival time)
  [ ] Keep trains only (remove bus / tram / boat)
  [ ] Remove cancelled stops and pass-throughs
  [ ] Duplicates
  [ ] Types / formats; station IDs that must match the station list
  [ ] Outliers (very large or negative delays) - choose and justify a limit
  [ ] Compute delay_min = actual - planned
  [ ] Join with the station list (canton)
  [ ] Save the row-count table to output/cleaning_report.csv
"""
from spark_session import OUTPUT_DIR, PARQUET_DIR, get_spark

report = []  # (step, rows_before, rows_after, reason)


def main():
    spark = get_spark("02_clean")
    df = spark.read.parquet(str(PARQUET_DIR / "stops_typed"))
    n = df.count()
    report.append(("start", n, n, "after ingestion"))

    # Example of one step:
    # before = df.count()
    # df = df.filter(df.actual_arrival.isNotNull())
    # report.append(("missing actual arrival", before, df.count(), "cannot compute delay"))

    for row in report:
        print(row)
    spark.stop()


if __name__ == "__main__":
    main()
