import pandas as pd
import statsmodels.api as sm


class Lowess:
    @classmethod
    def get_lowess_trend(cls, x, y):
        lowess_trend = sm.nonparametric.lowess(endog=y, exog=x)
        df = pd.DataFrame(lowess_trend, columns=["x", "y"])

        for i in range(1, len(df)):
            is_decreasing = df.loc[i, 'y'] < df.loc[i - 1, 'y']
            df.loc[i, 'slope'] = -1 if is_decreasing else 1

        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @classmethod
    def get_lowess_trendlines(cls, df):
        index = -1
        groups = []
        current_state = None

        for i in range(1, len(df)):
            has_changed = current_state != df.loc[i, 'slope']
            x, y = df.loc[i, 'x'], df.loc[i, 'y']
            if has_changed:
                current_state = df.loc[i, 'slope']
                groups.append({'x': [x], 'y': [y], 'slope': current_state})
                index += 1
            else:
                groups[index]['x'].append(x)
                groups[index]['y'].append(y)

        for trend in groups:
            trend["change"] = round(100*(1 - (min(trend['y'])/max(trend['y']))), 2)

        return groups
