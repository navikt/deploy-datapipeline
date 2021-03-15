import plotly.express as px
import plotly.io as pio
import dataverk
import datetime as dt
import os
import pandas
import logging
from google.cloud import storage
from io import StringIO
import time


class DeployDataPakke:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    BUCKET_NAME = "deployments-vera"
    PROJECT = "nais-analyse-prod-2dcc"

    def publiser_datapakke(self, file_uri):
        os.environ["DATAVERK_API_ENDPOINT"] = "https://data.nav.no/api"
        #os.environ["DATAVERK_BUCKET_ENDPOINT"] = "https://dv-api-intern.prod-gcp.nais.io/storage"
        os.environ["DATAVERK_BUCKET_ENDPOINT"] = "https://dv-api-ekstern.prod-gcp.nais.io/storage"
        #os.environ["DATAVERK_ES_HOST"] = "https://dv-api-intern.prod-gcp.nais.io/index/write/dcat"
        os.environ["DATAVERK_ES_HOST"] = "https://dv-api-ekstern.prod-gcp.nais.io/index/write/dcat"

        # Wait for istio
        time.sleep(60)

        dp = self.lag_datapakke(file_uri)
        dv = dataverk.Client()
        dv.publish(dp)

    def lag_datapakke(self, file_uri):
        metadata = self.create_metadata(title='Antall deployments av applikasjoner i NAV',
                                        description='''Nedbryting av antall deploys av applikasjoner til prod i NAV siden 2009. 
                                        Med "deploy" menes her endringer i en applikasjon som er satt i produksjon.
                                        Med "applikasjon" menes her programvare som er utviklet i eller for NAV av utviklere som jobber i eller for NAV. Dette kan være både interne verktøy og tjenester som inngår i selvbetjeningsløsningene på nav.no.
                                        Merk at datasettet kun inkluderer deployments til produksjon, altså at deployments til dev- og testmiljøer er ekskludert. Merk også at deploys av plattforminterne applikasjoner som kun tester om deploymekanismene fungerer er vasket bort da disse ville utgjort et betydelig antall deploys, men representerer "fiktive" deployhendelser.''',
                                        forfatter='Gøran Berntsen', forfatter_epost='goran.berntsen@nav.no')

        dp = dataverk.Datapackage(metadata)
        df = self.create_dataframe(file_uri)

        self.add_fig(dp, self.weekly_deploys_pr_year(df), "Gjennomsnittlig antall deploys hver uke per år (alle applikasjoner)")

        for år, view in self.app_pr_year(df).items():
            self.add_fig(dp, view, "Topp 5 deployet applikasjoner i {}".format(str(år)))

        self.add_fig(dp, self.deploys_pr_week(df), "Antall deploys per uke (alle applikasjoner) siste 5 år")
        self.add_fig(dp, self.deloys_pr_unique_apps(df), "Antall unike applikasjoner deployet per uke siste 5 år")
        self.add_fig(dp, self.deploys_pr_app_pr_week(df), "Gjennomsnittlig antall deploys per applikasjon per uke siste 5 år")
        self.add_fig(dp, self.lifespan(df), "Gjennomsnittlig tid mellom deploys av samme applikasjon per år")
        logging.info("created data package")

        return dp

    def create_metadata(self, title, description, forfatter, forfatter_epost, readme=''):
        return {'title': title,
                'description': description,
                'id': 'e1556a04a484bbe06dda2f6b874f3dc1',
                'readme': readme,
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
                'theme': [],
                'type': 'datapackage',
                'format': 'datapackage',
                'category': 'category',
                'provenance': 'NAV',
                'repo': 'https://github.com/navikt/deploy-datapipeline',
                'store': 'nais',
                'bucket': 'nav-opendata'
                }

    def add_fig(self, dp, view, name):
        dp.add_view(spec=pio.to_json(view), spec_type="plotly", name=name, title=name)

    def create_dataframe(self, file_uri):

        logging.info('initialize google storage client and access data product...')
        client = storage.Client()
        bucket = client.get_bucket(self.BUCKET_NAME)
        blob = bucket.get_blob('Mar-11-2021-deploys-vera.csv')
        data = blob.download_as_text()

        logging.info("initialize dataframe from data product...")
        df = pandas.read_csv(StringIO(data))
        logging.info(f'{len(df)} rows loaded into dataframe')

        logging.info("correct data types (from string conversion)...")
        df['deployed_timestamp'] = pandas.to_datetime(df['deployed_timestamp'], format='%Y-%m-%d %H:%M:%S')
        df['replaced_timestamp'] = pandas.to_datetime(df['replaced_timestamp'], format='%Y-%m-%d %H:%M:%S')

        logging.info("filter out nais-deploy-canary...")
        df = df[df['application'] != 'nais-deploy-canary']

        logging.info("derive relevant date columns...")
        df['dato'] = df['deployed_timestamp'].dt.date
        df['ukenr'] = df['deployed_timestamp'].dt.isocalendar().week.astype('str')
        df['ukenr'] = df['ukenr'].apply( lambda x: x.zfill(2))
        df['uke'] = df['deployed_timestamp'].dt.isocalendar().year.astype('str') + '-' + df['ukenr']
        df['år'] = df['deployed_timestamp'].dt.isocalendar().year
        df['app'] = df['application']
        df['lifetime'] = (df['replaced_timestamp'] - df['deployed_timestamp']).astype('timedelta64[s]')
        logging.info(f'final dataframe with {len(df)} rows ready')

        return df

    def app_pr_year(self, df):
        figs = {}
        df = df.sort_values("år")
        for år in df['år'].unique():
            apps = df[df['år'] == år].groupby('app').size().reset_index(name='antall').sort_values('antall',
                                                                                                   ascending=False)
            fig = px.bar(apps.head(5), x='app', y='antall', title=f'Topp 5 deployet applikasjoner i {str(år)}')
            figs[år] = fig
        return figs

    def deploys_pr_week(self, df):
        uker = df.groupby(['uke']).size().reset_index(name='antall').sort_values('uke')
        fig = px.bar(uker.tail(5 * 52), x='uke', y='antall', title='Antall deploys per uke siste 5 år (alle applikasjoner)')
        fig.update_xaxes(type='category')
        fig.update_layout(hovermode="x unified")
        return fig

    def weekly_deploys_pr_year(self, df):
        år = df.groupby(['uke', 'år']).size().reset_index(name='antall') \
            .groupby('år').agg(snitt_deploys_per_uke=('antall', 'mean')).reset_index()
        år['snitt_deploys_per_uke'] = år['snitt_deploys_per_uke'].round(0)
        fig = px.bar(år, x='år', y='snitt_deploys_per_uke', title='Gjennomsnittlig antall deploys hver uke per år (alle applikasjoner)')
        fig.update_xaxes(type='category')
        return fig

    def deloys_pr_unique_apps(self, df):
        uke_app = df.groupby(['uke', 'år', 'application']).size().reset_index(name='antall').sort_values('uke')
        uke_app = uke_app.groupby(['uke', 'år']).size().reset_index(name='antall_apps').sort_values('uke')
        fig = px.bar(uke_app.tail(5*52), x='uke', y='antall_apps', title='Antall unike applikasjoner deployet per uke siste 5 år')
        fig.update_xaxes(type='category')
        fig.update_layout(hovermode="x unified")
        return fig

    def deploys_pr_app_pr_week(self, df):
        uke_app_snitt = df.groupby(['uke', 'år', 'application']).size().reset_index(name='antall').sort_values('uke')
        uke_app_snitt = uke_app_snitt.groupby(['uke', 'år']).agg(snitt_deploys=('antall', 'mean')).reset_index()
        fig = px.bar(uke_app_snitt.tail(5*52), x='uke', y='snitt_deploys',
                     title='Gjennomsnittlig antall deploys per applikasjon per uke siste 5 år')
        fig.update_xaxes(type='category')
        fig.update_layout(hovermode="x unified")
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
