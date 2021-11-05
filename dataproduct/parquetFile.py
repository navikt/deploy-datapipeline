import logging
from google.cloud import storage
import pandas
import os


def create_dataframe(filename):
    logging.info("initialize dataframe from data product...")

    df = pandas.read_parquet(filename)
    logging.info(f'{len(df)} rows loaded into dataframe')

    logging.info("filter out nais-deploy-canary...")
    df = df[df['application'] != 'nais-deploy-canary']
    logging.info("filter out testapp-storage...")
    df = df[df['application'] != 'testapp-storage']
    logging.info("filter out kafkarator-canary...")
    df = df[df['application'] != 'kafkarator-canary']

    logging.info("derive relevant date columns...")
    df['dato'] = df['deployed_timestamp'].dt.date
    df['ukenr'] = df['deployed_timestamp'].dt.isocalendar().week.astype('str')
    df['ukenr'] = df['ukenr'].apply(lambda x: x.zfill(2))
    df['uke'] = df['deployed_timestamp'].dt.isocalendar().year.astype('str') + '-' + df['ukenr']
    df['måned'] = df['deployed_timestamp'].dt.month
    df['måned'] = df['måned'].astype('str').apply(lambda x: x.zfill(2))
    df['måned'] = df['deployed_timestamp'].dt.isocalendar().year.astype('str') + '-' + df['måned']
    df['år'] = df['deployed_timestamp'].dt.isocalendar().year
    df['app'] = df['application']
    df['lifetime'] = (df['replaced_timestamp'] - df['deployed_timestamp']).astype('timedelta64[s]')
    logging.info(f'final dataframe with {len(df)} rows ready')

    return df
