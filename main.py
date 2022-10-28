import pandas as pd
from flask_bootstrap import Bootstrap
from flask import Flask, render_template
from wtforms import StringField, FloatField, SelectField
from wtforms.validators import NumberRange, InputRequired
from flask_wtf import FlaskForm
import googlemaps
import utm
import numpy as np
import base64
from io import BytesIO
from matplotlib.figure import Figure

gmaps = googlemaps.Client(key='AIzaSyBljNPdIwJuFiq3f7wXSjZmL2Sn2z66cTs')

app = Flask(__name__)
app.secret_key = '<3 03'
Bootstrap(app)

data = pd.read_csv('data2.csv', index_col=0)

# Factor de Zona
# Numero de zona - Z
table_Z = [('Z4', 0.10),
           ('Z3', 0.25),
           ('Z2', 0.35),
           ('Z1', 0.45), ]
# Factor de Suelo
# Zi, Si(Tipo de Suelo)
soil_type = [('S0', 'Roca Dura'),
             ('S1', 'Roca o Suelos Muy Rígidos'),
             ('S2', 'Suelos Intermedios'),
             ('S3', 'Suelos Blandos')]
table_S = [[0.80, 1.00, 1.60, 2.00],
           [0.80, 1.00, 1.20, 1.40],
           [0.80, 1.00, 1.15, 1.20],
           [0.80, 1.00, 1.05, 1.10]]
# Si(Tipo de Suelo)
table_Tp = [0.3, 0.4, 0.6, 1.0]
table_Tl = [3.0, 2.5, 2.0, 1.6]
# Factor de Uso
table_U = [('A', 'Edificaciones Esenciales', 1.5),
           ('B', 'Edificaciones Importantes', 1.3),
           ('C', 'Edificaciones Comunes', 1.0),
           ('D', 'Edificaciones Temporales'), None]
# Period
T = np.linspace(0, 2.5, 32)


# Factor de Amplificación Sísmica
def fun_C(T, Tp, Tl):
    result = np.where(T < Tp, 2.5, 2.5 * Tp / T)
    result = np.where(T > Tl, 2.5 * Tp * Tl / T ** 2, result)
    return result


# Gravedad
g = 981  # cm/s^2


# Graph T vs Sa
def graph_T_Sa(T, Sa):
    # Generate the figure **without using pyplot**.
    fig = Figure(figsize=(6, 4), dpi=80)
    ax = fig.subplots()
    ax.set_title("T vs Sa")

    ax.plot(T, Sa)

    ax.axis([0, max(T), 0.8*min(Sa), 1.2*max(Sa)])
    ax.set_xlabel('T(s)')
    ax.set_ylabel('Sa(cm/s)')
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    return f"data:image/png;base64,{base64.b64encode(buf.getbuffer()).decode('ascii')}"

class AddressForm(FlaskForm):
    address = StringField(label='Dirección', id="autocomplete",
                          render_kw={"placeholder": "Ingresa una dirección o Lugar"}, validators=[InputRequired()])
    soil = SelectField(label='Perfil de Suelo (S)', choices=[(0, 'Perfil Tipo S0: Roca Dura'),
                                                             (1, 'Perfil Tipo S1: Roca o Suelos Muy Rígidos'),
                                                             (2, 'Perfil Tipo S2: Suelos Intermedios'),
                                                             (3, 'Perfil Tipo S3: Suelos Blandos'),
                                                             (4, 'Perfil Tipo S4: Condiciones Excepcioneales')],
                       validators=[InputRequired()])
    use = SelectField(label='Factor de Uso (U)', choices=[(0, 'A: Edificaciones Esenciales'),
                                                          (1, 'B: Edificaciones Importantes'),
                                                          (2, 'C: Edificaciones Comunes'),
                                                          (3, 'D: Edificaciones Temporales')],
                      validators=[InputRequired()])


class LatlonForm(FlaskForm):
    latitude = FloatField(label='Latitud', render_kw={"placeholder": "Ingresa una Latitud"},
                          validators=[InputRequired(), NumberRange()])
    longitude = FloatField(label='Longitud', render_kw={"placeholder": "Ingresa una Longitud"},
                           validators=[InputRequired(), NumberRange()])
    soil = SelectField(label='Perfil de Suelo (S)', choices=[(0, 'Perfil Tipo S0: Roca Dura'),
                                                             (1, 'Perfil Tipo S1: Roca o Suelos Muy Rígidos'),
                                                             (2, 'Perfil Tipo S2: Suelos Intermedios'),
                                                             (3, 'Perfil Tipo S3: Suelos Blandos'),
                                                             (4, 'Perfil Tipo S4: Condiciones Excepcioneales')],
                       validators=[InputRequired()])
    use = SelectField(label='Factor de Uso (U)', choices=[(0, 'A: Edificaciones Esenciales'),
                                                          (1, 'B: Edificaciones Importantes'),
                                                          (2, 'C: Edificaciones Comunes'),
                                                          (3, 'D: Edificaciones Temporales')],
                      validators=[InputRequired()])


class UtmForm(FlaskForm):
    east = FloatField(label='Este', render_kw={"placeholder": "Ingresa un valor para el Este"},
                      validators=[InputRequired(), NumberRange()])
    north = FloatField(label='Norte', render_kw={"placeholder": "Ingresa un valor para el Norte"},
                       validators=[InputRequired(), NumberRange()])
    zone = SelectField(label='Zona', choices=[(17, 'Zona 17'), (18, 'Zona 18'), (19, 'Zona 19')],
                       validators=[InputRequired()])
    soil = SelectField(label='Perfil de Suelo (S)', choices=[(0, 'Perfil Tipo S0: Roca Dura'),
                                                             (1, 'Perfil Tipo S1: Roca o Suelos Muy Rígidos'),
                                                             (2, 'Perfil Tipo S2: Suelos Intermedios'),
                                                             (3, 'Perfil Tipo S3: Suelos Blandos'),
                                                             (4, 'Perfil Tipo S4: Condiciones Excepcioneales')],
                       validators=[InputRequired()])
    use = SelectField(label='Factor de Uso (U)', choices=[(0, 'A: Edificaciones Esenciales'),
                                                          (1, 'B: Edificaciones Importantes'),
                                                          (2, 'C: Edificaciones Comunes'),
                                                          (3, 'D: Edificaciones Temporales')],
                      validators=[InputRequired()])


@app.route("/", methods=['GET', 'POST'])
def home():
    forms = {'address': AddressForm(),
             'latlon': LatlonForm(),
             'utm': UtmForm()}

    values = {'address': 'Av. Túpac Amaru 210, Rímac 15333, Peru',
              'postal_code': 15333,
              'Z': ('Z4', 0.10),
              'U': ('A', 'Edificaciones Esenciales', 1.5),
              'Stype': ('S0', 'Roca Dura'),
              'S': 0.8,
              'Tp': 0.3,
              'Tl': 3.0,
              'T': T,
              'C': fun_C(T, 0.3, 3.0),
              'Sa': 0.45 * 1.5 * fun_C(T, 0.3, 3.0) * 0.8 * g,
              'image': graph_T_Sa(T, 0.45 * 1.5 * fun_C(T, 0.3, 3.0) * 0.8 * g),
              'input_view': 'address',
              'geo_coord': (-12.0238022, -77.0505946),
              'utm_coord': (276749.88, 8669981.89, 18, 'L'),
              'inperu': True}

    if forms["address"].validate_on_submit():
        address = forms["address"].address.data
        soil = int(forms['address'].soil.data)
        use = int(forms['address'].use.data)

        geocode_result = gmaps.geocode(address)
        if geocode_result:
            if 'formatted_address' in geocode_result[0] and 'address_components' in geocode_result[0] and 'geometry' in \
                    geocode_result[0]:
                formatted_address = geocode_result[0]['formatted_address']

                for element in geocode_result[0]['address_components']:
                    if 'postal_code' in element['types']:
                        postal_code = element['long_name']

                latitude = geocode_result[0]['geometry']['location']['lat']
                longitude = geocode_result[0]['geometry']['location']['lng']
                utm_coord = utm.from_latlon(latitude, longitude)

                if postal_code.isdigit() and int(postal_code) in data.index:
                    zone = data.loc[int(postal_code)]['z']
                    Z = table_Z[zone - 1]
                    U = table_U[use]
                    Stype = soil_type[soil]
                    S = table_S[zone - 1][soil]
                    Tp = table_Tp[soil]
                    Tl = table_Tl[soil]
                    C = fun_C(T, Tp, Tl)
                    Sa = Z[1] * U[2] * C * S * g

                    values = {'address': formatted_address,
                              'postal_code': postal_code,
                              'Z': Z,
                              'U': U,
                              'Stype': Stype,
                              'S': S,
                              'Tp': Tp,
                              'Tl': Tl,
                              'T': T,
                              'C': C,
                              'Sa': Sa,
                              'image': graph_T_Sa(T, Sa),
                              'input_view': 'address',
                              'geo_coord': (latitude, longitude),
                              'utm_coord': utm_coord,
                              'inperu': True}
                else:
                    values = {'address': formatted_address,
                              'postal_code': postal_code,
                              'input_view': 'address',
                              'geo_coord': (latitude, longitude),
                              'utm_coord': utm_coord,
                              'inperu': False}

    if forms["latlon"].validate_on_submit():
        latitude = forms["latlon"].latitude.data
        longitude = forms["latlon"].longitude.data
        utm_coord = utm.from_latlon(latitude, longitude)

        geocode_result = gmaps.reverse_geocode(latlng=(latitude, longitude))
        if geocode_result:
            if 'formatted_address' in geocode_result[0] and 'address_components' in geocode_result[0]:
                formatted_address = geocode_result[0]['formatted_address']

                for element in geocode_result[0]['address_components']:
                    if 'postal_code' in element['types']:
                        postal_code = element['long_name']

                        if postal_code.isdigit() and int(postal_code) in data.index:
                            zone = data.loc[int(postal_code)]['z']
                            Z = table_Z[zone - 1]
                            values = {'address': formatted_address,
                                      'postal_code': postal_code,
                                      'zone': zone,
                                      'Z': Z,
                                      'input_view': 'latlon',
                                      'geo_coord': (latitude, longitude),
                                      'utm_coord': utm_coord,
                                      'inperu': True}
                        else:
                            values = {'address': formatted_address,
                                      'postal_code': postal_code,
                                      'input_view': 'latlon',
                                      'geo_coord': (latitude, longitude),
                                      'utm_coord': utm_coord,
                                      'inperu': False}
                    else:
                        values = {'address': formatted_address,
                                  'input_view': 'latlon',
                                  'geo_coord': (latitude, longitude),
                                  'utm_coord': utm_coord,
                                  'inperu': False}

    if forms["utm"].validate_on_submit():
        north = float(forms["utm"].north.data)
        east = float(forms["utm"].east.data)
        zone = int(forms["utm"].zone.data)

        latitude, longitude = utm.to_latlon(east, north, zone, 'L')
        utm_coord = (east, north, zone, 'L')

        geocode_result = gmaps.reverse_geocode(latlng=(latitude, longitude))
        if geocode_result:
            if 'formatted_address' in geocode_result[0] and 'address_components' in geocode_result[0]:
                formatted_address = geocode_result[0]['formatted_address']

                for element in geocode_result[0]['address_components']:
                    if 'postal_code' in element['types']:
                        postal_code = element['long_name']

                if postal_code.isdigit() and int(postal_code) in data.index:
                    zone = data.loc[int(postal_code)]['z']
                    Z = table_Z[zone - 1]
                    values = {'address': formatted_address,
                              'postal_code': postal_code,
                              'zone': zone,
                              'Z': Z,
                              'input_view': 'address',
                              'geo_coord': (latitude, longitude),
                              'utm_coord': utm_coord,
                              'inperu': True}
                else:
                    values = {'address': formatted_address,
                              'postal_code': postal_code,
                              'input_view': 'address',
                              'geo_coord': (latitude, longitude),
                              'utm_coord': utm_coord,
                              'inperu': False}

    return render_template('index.html', values=values, forms=forms)


if __name__ == '__main__':
    app.run(debug=True)
