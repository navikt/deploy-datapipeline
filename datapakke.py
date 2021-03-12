import plotly.express as px
import plotly.io as pio
import dataverk
import datetime as dt
import os
import pandas
import logging
from google.cloud import storage
from io import BytesIO


class DeployDataPakke:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    BUCKET_NAME = "deployments-vera"
    PROJECT = "nais-analyse-prod-2dcc"

    def publiser_datapakke(self, file_uri):
        os.environ["DATAVERK_API_ENDPOINT"] = "https://data.intern.nav.no/api"
        os.environ["DATAVERK_BUCKET_ENDPOINT"] = "https://dv-api-intern.prod-gcp.nais.io/storage"
        os.environ["DATAVERK_ES_HOST"] = "https://dv-api-intern.prod-gcp.nais.io/index/write/dcat"

        dp = self.lag_datapakke(file_uri)
        dv = dataverk.Client()
        dv.publish(dp)

    def lag_datapakke(self, file_uri):
        metadata = self.create_metadata(titel='Deployment av applikasjon i NAV',
                                        description='Viser antall deploys av applikasjoner i NAV siden 2009.',
                                        forfatter='Gøran Berntsen', forfatter_epost='goran.berntsen@nav.no')

        dp = dataverk.Datapackage(metadata)
        df = self.create_dataframe(file_uri)
        for år, view in self.app_pr_year(df).items():
            self.add_fig(dp, view, "Mest deployet apps i {}".format(str(år)))

        self.add_fig(dp, self.deploys_pr_week(df), "deploys per uke")
        self.add_fig(dp, self.deloys_pr_unique_apps(df), "unike applikasjoner deployet pr uke")
        self.add_fig(dp, self.deploys_pr_app_pr_week(df), "gjennomsnittlig deploys pr app pr uke")
        self.add_fig(dp, self.lifespan(df), "gjennomsnittlig tid mellom deploys av samme applikasjon pr år")
        logging.info("created data package")

        return dp

    def create_metadata(self, titel, description, forfatter, forfatter_epost):
        return {'title': titel,
                'description': description,
                'readme': '',
                'accessRights': 'Open',
                'issued': dt.datetime.now().isoformat(),
                'modified': dt.datetime.now().isoformat(),
                'language': 'Norsk',
                'periodicity': '',
                'temporal': {'from': f'2009-01-01', 'to': f'{dt.datetime.now().isoformat()}'},
                'author': forfatter,
                'publisher': {'name': 'nais', 'url': 'https://nais.io'},
                'contactpoint': {'name': forfatter, 'email': forfatter_epost},
                'license': {'name': 'CC BY 4.0', 'url': 'http://creativecommons.org/licenses/by/4.0/deed.no'},
                'keywords': [],
                'spatial': '',
                'theme': [],
                'type': 'datapackage',
                'format': 'datapackage',
                'category': 'category',
                'provenance': 'NAV',
                'repo': '',
                'notebook': '',
                'store': 'nais',
                'project': 'odata',
                'bucket': 'nav-opendata'
                }

    def add_fig(self, dp, view, name):
        dp.add_view(spec=pio.to_json(view), spec_type="plotly", name=name, title=name)

    def create_dataframe(self, file_uri):
        client = storage.Client()
        bucket = client.get_bucket(self.BUCKET_NAME)
        blob = bucket.get_blob(file_uri)
        #data = blob.download_as_text()

        # df = pandas.read_csv("gs://" + self.BUCKET_NAME + "/" + file_uri)
        # df = pandas.DataFrame()

        logging.info("read fil from bucket")

        byte_stream = BytesIO()
        blob.download_to_file(byte_stream.decode("utf-8") )
        byte_stream.seek(0)

        df = pandas.read_csv(byte_stream)

        logging.info("head: " + df.head(5))

        logging.info("extrated dataframe")

        df = df[df['application'] != 'nais-deploy-canary']
        df['dato'] = df['deployed_timestamp'].dt.date
        df['ukenr'] = df['deployed_timestamp'].dt.isocalendar().week.astype('str')
        df['ukenr'] = df['ukenr'].apply(lambda x: x.zfill(2))
        df['uke'] = df['deployed_timestamp'].dt.isocalendar().year.astype('str') + '-' + df['ukenr']
        df['år'] = df['deployed_timestamp'].dt.isocalendar().year
        df['app'] = df['application']
        df['lifetime'] = (df['replaced_timestamp'] - df['deployed_timestamp']).astype('timedelta64[s]')
        return df

    def app_pr_year(self, df):
        figs = {}
        df = df.sort_values("år")
        for år in df['år'].unique():
            apps = df[df['år'] == år].groupby('app').size().reset_index(name='antall').sort_values('antall',
                                                                                                   ascending=False)
            fig = px.bar(apps.head(5), x='app', y='antall', title=str(år))
            figs[år] = fig
        return figs

    def deploys_pr_week(self, df):
        uker = df.groupby(['uke']).size().reset_index(name='antall').sort_values('uke')
        fig = px.bar(uker.tail(5 * 52), x='uke', y='antall', title='Deploys per uke siste 5 år')
        fig.update_xaxes(type='category')
        return fig

    def deploys_pr_week(self, df):
        år = df.groupby(['uke', 'år']).size().reset_index(name='antall') \
            .groupby('år').agg(snitt_deploys_per_uke=('antall', 'mean')).reset_index()
        år['snitt_deploys_per_uke'] = år['snitt_deploys_per_uke'].round(0)
        fig = px.bar(år, x='år', y='snitt_deploys_per_uke', title='Gjennomsnittlig deploys per uke')
        fig.update_xaxes(type='category')
        return fig

    def deloys_pr_unique_apps(self, df):
        uke_app = df.groupby(['uke', 'år', 'application']).size().reset_index(name='antall').sort_values('uke')
        uke_app = uke_app.groupby(['uke', 'år']).size().reset_index(name='antall_apps').sort_values('uke')
        fig = px.bar(uke_app, x='uke', y='antall_apps', title='Antall unike applikasjoner deployet per uke')
        fig.update_xaxes(type='category')
        return fig

    def deploys_pr_app_pr_week(self, df):
        uke_app_snitt = df.groupby(['uke', 'år', 'application']).size().reset_index(name='antall').sort_values('uke')
        uke_app_snitt = uke_app_snitt.groupby(['uke', 'år']).agg(snitt_deploys=('antall', 'mean')).reset_index()
        fig = px.bar(uke_app_snitt, x='uke', y='snitt_deploys',
                     title='Gjennomsnitt antall deploys per applikasjon per uke')
        fig.update_xaxes(type='category')
        return fig

    def display_time(self, seconds, granularity=2):
        intervals = (
            ('weeks', 604800),  # 60 * 60 * 24 * 7
            ('days', 86400),  # 60 * 60 * 24
            ('hours', 3600),  # 60 * 60
            ('minutes', 60),
            ('seconds', 1),
        )
        result = []

        for name, count in intervals:
            value = int(seconds // count)
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    def lifespan(self, df):
        levetid = df[df['deployed_timestamp'] < df['replaced_timestamp']].groupby('år').agg(
            snitt_levetid_sekunder=('lifetime', 'mean')).reset_index()
        levetid['pretty_snitt_levetid'] = levetid['snitt_levetid_sekunder'].apply(lambda x: self.display_time(x))
        levetid['snitt_levetid_timer'] = (levetid['snitt_levetid_sekunder'] / (60 * 60)).astype(int)
        levetid = levetid[['år', 'pretty_snitt_levetid', 'snitt_levetid_timer']]
        fig = px.bar(levetid, x='år', y='snitt_levetid_timer',
                     title='Gjennomsnittlig tid mellom deploys for en app (i timer) per år')
        fig.update_xaxes(type='category')
        return fig
