"""
STEP 1 - INGESTION: raw CSV -> typed Parquet tables.   Owner: <name>

TODO:
  [ ] Run scripts/inspect_raw.py and copy the real column names below.
  [ ] Write the explicit schema (StructType) for the Ist-Daten CSV.
  [ ] Write the explicit schema for the station list (service points).
  [ ] Convert dates/timestamps to real types (format: dd.MM.yyyy HH:mm ?).
  [ ] Write both tables to data/parquet/ and print the row counts.
"""
from pyspark.sql.types import StringType, StructField, StructType

from spark_session import PARQUET_DIR, RAW_DIR, get_spark

# Explicit schema: fill in after looking at the real file header.
ISTDATEN_SCHEMA = StructType([
    StructField("BETRIEBSTAG", StringType(), True),        # operating day
    StructField("HALTESTELLEN_NAME", StringType(), True),  # station name
    # TODO: add every column of the file, in the same order
])


def main():
    spark = get_spark("01_ingest")

    df = (spark.read
          .option("header", True)
          .option("sep", ";")
          .schema(ISTDATEN_SCHEMA)
          .csv(str(RAW_DIR / "istdaten" / "*.csv")))

    df.printSchema()
    df.show(5, truncate=False)
    print("rows:", df.count())

    # TODO: convert types, then:
    # df.write.mode("overwrite").parquet(str(PARQUET_DIR / "stops_typed"))

    spark.stop()


if __name__ == "__main__":
    main()
