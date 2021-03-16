import pandas
import deploydataproduct
import os


def test_parquet_conversion():
    csv = 'test.csv'
    filename = 'test.parquet'
    deploy = deploydataproduct.DeployDataProduct()

    csv_text = open(csv, 'r').read()

    deploy.transform(csv_text, filename)

    df = pandas.read_parquet(filename)

    print(df['deployed_timestamp'][0])
    print(df['replaced_timestamp'][0])

    assert type(df['deployed_timestamp'][0]) == pandas.Timestamp
    assert type(df['replaced_timestamp'][0]) == pandas.Timestamp

    os.remove(filename)


