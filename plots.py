import plotext as plt
import plotly.express as px


class Plotter:

    @classmethod
    def plot(cls, **kwargs):
        if kwargs.get("_type") == "terminal":
            del kwargs["_type"]
            width, height, last_sign, last_change = cls.plot_terminal(**kwargs)
            return width, height, last_sign, last_change
        elif kwargs.get("_type") == "web":
            del kwargs["_type"]
            cls.plot_plotly(**kwargs)
        else:
            raise NotImplementedError("Please specify plot type")

    @classmethod
    def plot_plotly(cls, x, y, trendlines=None, title=None, xaxis_title=None, yaxis_title=None):
        fig = px.line(x=x, y=y, title=title)
        if trendlines:
            for i, tl in enumerate(trendlines, start=1):
                sign = '+' if tl["slope"] > 0 else '-'
                fig.add_scatter(x=tl['x'], y=tl['y'], text=f'slope: {tl["slope"]}', name=f'({sign}) trend {i}')

        if any([title, xaxis_title, yaxis_title]):
            fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title)

        fig.show()

    @classmethod
    def plot_terminal(cls, x, y, trendlines=None, title=None, xaxis_title=None, yaxis_title=None):
        plt.clp()
        plt.clt()
        plt.plot(x, y, label=title, line_color="artic")

        last_sign, last_change = None, None

        if trendlines:
            for i, tl in enumerate(trendlines, start=1):
                sign = '+' if tl["slope"] > 0 else '-'
                plt.plot(tl['x'], tl['y'], label=f'({sign} {tl["change"]}%) trend {i}')

                last_sign = sign
                last_change = tl["change"]

        if any([title, xaxis_title, yaxis_title]):
            plt.title(title)
            plt.xlabel(xaxis_title)
            plt.ylabel(yaxis_title)

        width, height = plt.terminal_size()
        width, height = (width, int(height * 0.75))
        plt.figsize(width, height)
        plt.grid(True)
        plt.canvas_color("black")
        plt.axes_color("black")
        plt.ticks_color("white")
        plt.show()
        return width, height, last_sign, last_change
