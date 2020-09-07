import dash 
import dash_html_components as html
import dash_core_components as dcc

#risky code: is it possible to instantiate an empty Dash object and later set it equal to the declared server in create_dashboard?
dash_app_local = dash.Dash()

def create_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = dash.Dash(__name__,
                         server=server,
                         routes_pathname_prefix='/dashapp2/',
                         external_stylesheets=['/static/css/styles.css']
                         )
    dash_app_local = dash_app.server
    return dash_app.server

# Create Dash Layout
@dash_app_local.server.route('/dashapp2/opponent1/opponent2')
def teamsSelected(opponent1, opponent2):    
    def basechart2(opponent1, opponent2):
        dash_app_local.layout  = html.Div(children=[
        html.H1(children='Hello Dash'),

        html.Div(children='''
        Dash: A web application framework for Python.
    '''),

        dcc.Graph(
        id='example-graph',
            figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
])

    return dash_app_local.server
