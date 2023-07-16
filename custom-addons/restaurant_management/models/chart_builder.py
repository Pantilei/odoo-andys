
from statistics import mean

import plotly.graph_objects as go


class ChartBuilder:
    def __init__(
            self,
            plot_bgcolor = 'rgba(0,0,0,0)',
            paper_bgcolor = 'rgba(0,0,0,0)',
            height = 1000
            # height = 350
        ) -> None:
        self._plot_bgcolor = plot_bgcolor
        self._paper_bgcolor = paper_bgcolor
        self._height = height

    def build_horizontal_bar_chart(self, x, y):
        y_cut = [item if len(item) <= 39 else f"{item[:39]}..." for item in y]
        annotations = [
            dict(
                xref='paper', 
                yref='y',
                x=0.06, 
                # x=0.19, 
                y=yd,
                xanchor='center',
                text=str(yd),
                font=dict(family='Arial', size=14, color='white'),
                showarrow=False, 
                # align='center'
            ) for yd in y_cut
        ]
        for x_val, y_val in zip(x, y_cut):
            annotations.append(dict(
                xref="x",
                yref="y",
                x=x_val*1.02,
                y=y_val,
                text=x_val,
                font=dict(family='Arial', size=12, color='white'),
                showarrow=False,
                xanchor='left',
                align='right'
            ))
        layout = go.Layout(
            # title='Double Line Chart',
            xaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'), 
                showgrid=False,
                showline=False,
                showticklabels=False,
                dtick=True,
                zeroline=False,
                domain=[0.2, 1],
            ),
            yaxis=dict( 
                showticklabels=False,
                domain=[0, 1],
                titlefont=dict(color='white')
            ),
            autosize=True,
            height=self._height,
            plot_bgcolor=self._paper_bgcolor,
            paper_bgcolor=self._paper_bgcolor,
            margin=dict(l=100, r=1, b=1, t=1, pad=1),
            dragmode=False,
            annotations=annotations
        )

        # Create the bar chart using plotly
        fig = go.Figure(data=go.Bar(
            x=x,  # Use values as the x-axis values
            y=y_cut,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={
                "color": ["#71EDF1" for _ in y],
            },
            texttemplate=' ',  # Use %{y} to display the category names as labels
            hovertemplate='Кол-во: %{x}<br>Ошибка: %{text}<extra></extra>', 
            text=y,
            textposition='auto',  # Set the position of the labels
        ), layout=layout)

        config = {'displayModeBar': False}
        
        return fig.to_html(config=config)
    
    def build_grouped_horizontal_bar_chart(self, y, x1, x2, label1, label2):
        colors = ("#46A1BF", "#5cc4cc")
        y_cut = [item if len(item) <= 39 else f"{item[:39]}..." for item in y]
        annotations = [
            dict(
                xref='paper', 
                yref='y',
                x=0.06, 
                y=y_point,
                xanchor='center',
                text=str(y_point_cut),
                font=dict(family='Arial', size=12, color='white'),
                showarrow=False, 
                # align='center'
            ) for y_point, y_point_cut in zip(y, y_cut)
        ]
        for (i, yp), xp in zip(enumerate(y), x1):
            annotations.append(
                dict(
                    xref="x",
                    yref="y",
                    x=xp,
                    y=i-0.23,
                    xanchor='left',
                    text=xp,
                    font=dict(family='Arial', size=12, color='white'),
                    showarrow=False
                )
            )

        for (i, yp), xp in zip(enumerate(y), x2):
            annotations.append(
                dict(
                    xref="x",
                    yref="y",
                    x=xp,
                    y=i+0.23,
                    xanchor='left',
                    text=xp,
                    font=dict(family='Arial', size=12, color='white'),
                    showarrow=False
                )
            )

        layout = go.Layout(
            # title='Double Line Chart',
            xaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'), 
                showgrid=False,
                showline=False,
                zeroline=False,
                showticklabels=False,
                domain=[0.2, 1],
            ),
            yaxis=dict( 
                showticklabels=False,
                domain=[0, 1],
                titlefont=dict(color='white'),
                autorange="reversed"
            ),
            autosize=True,
            height=self._height,
            plot_bgcolor=self._paper_bgcolor,
            paper_bgcolor=self._paper_bgcolor,
            margin=dict(l=100, r=1, b=1, t=1, pad=1),
            legend=dict(font=dict(color="white")),
            dragmode=False,
            annotations=annotations,
            barmode="group",
            # hovermode="closest"
        )

        # Create the bar chart using plotly
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name=label1,
            x=x1,  # Use values as the x-axis values
            y=y,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={"color": [colors[0] for _ in y]},
            hovertemplate='Кол-во ошибок / ед проверки: %{x}<br>Департамент: %{y}<extra></extra>', 
            # texttemplate='%{y}',  # Use %{y} to display the category names as labels
            # textposition='auto',  # Set the position of the labels
        ))

        fig.add_trace(go.Bar(
            name=label2,
            x=x2,  # Use values as the x-axis values
            y=y,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={"color": [colors[1] for _ in y]},
            # texttemplate='%{y}',  # Use %{y} to display the category names as labels
            # textposition='auto',  # Set the position of the labels
        ))

        fig.update_layout(layout)

        config = {'displayModeBar': False}
        
        return fig.to_html(config=config)
    
    def build_year_to_year_line_chart(self, x, y1, y2, label1, label2, upper_limit):
        colors = ("#46A1BF", "#5cc4cc")
        # Create the first line chart trace
        trace1 = go.Scatter(
            x=x,
            y=y1,
            mode='lines+markers',
            marker=dict(size=10),
            name=label1,
            line=dict(color=colors[0])
        )

        # Create the second line chart trace
        trace2 = go.Scatter(
            x=x,
            y=y2,
            mode='lines+markers',
            marker=dict(size=10),
            name=label2,
            line=dict(color=colors[1])
        )

        # Combine the traces into a data object
        data = [trace1, trace2]

        # Create the layout for the chart
        layout = go.Layout(
            # title='Double Line Chart',
            xaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'), 
                showgrid=False,
            ),
            yaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'),
                range=[0, upper_limit]
            ),
            autosize=True,
            height=self._height,
            plot_bgcolor=self._plot_bgcolor,
            paper_bgcolor=self._paper_bgcolor,
            showlegend=True,
            dragmode=False,
            legend=dict(x=0.5, y=1.1, orientation='h', yanchor='top', xanchor='center', font=dict(color="white")),
            margin=dict(l=1, r=1, b=1, t=1, pad=1),
        )

        # Create the chart object
        fig = go.Figure(data=data, layout=layout)

        y1_mean = round(mean(y1), 2)
        fig.add_hline(
            y=y1_mean, 
            line_width=3, 
            line_dash="dash", 
            line_color=colors[0],
            annotation=dict(
                xref='paper', 
                yref='y',
                x=0, 
                y=y1_mean*1 or 0.1,
                xanchor='left',
                text=f"{y1_mean}",
                font=dict(family='Arial', size=12, color=colors[0]),
                showarrow=False, 
                align='right'
            )
        )
        y2_mean = round(mean(y2), 2)
        fig.add_hline(
            y=y2_mean, 
            line_width=3, 
            line_dash="dash", 
            line_color=colors[1],
            annotation=dict(
                xref='paper', 
                yref='y',
                x=0, 
                y=y2_mean or 0.1,
                xanchor='left',
                text=f"{y2_mean}",
                font=dict(family='Arial', size=12, color=colors[1]),
                showarrow=False, 
                align='right'
            )
        )
        
        config = {'displayModeBar': False}

        return fig.to_html(config=config)  
