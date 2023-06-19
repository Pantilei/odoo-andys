
import plotly.graph_objects as go


class ChartBuilder:
    def __init__(
            self,
            plot_bgcolor = 'rgba(0,0,0,0)',
            paper_bgcolor = 'rgba(0,0,0,0)',
            height = 350
        ) -> None:
        self._plot_bgcolor = plot_bgcolor
        self._paper_bgcolor = paper_bgcolor
        self._height = height

    def build_horizontal_bar_chart(self, x, y):
        layout = go.Layout(
            # title='Double Line Chart',
            xaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'), 
                showgrid=True,
                domain=[0.5, 1],
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
            annotations=[
                dict(
                    xref='paper', 
                    yref='y',
                    x=0.5, 
                    y=yd,
                    xanchor='right',
                    text=str(yd),
                    font=dict(family='Arial', size=12, color='white'),
                    showarrow=False, 
                    align='right'
                ) for yd in y
            ]
        )

        # Create the bar chart using plotly
        fig = go.Figure(data=go.Bar(
            x=x,  # Use values as the x-axis values
            y=y,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={"color": ["#71EDF1" for _ in y]},
            # texttemplate='%{y}',  # Use %{y} to display the category names as labels
            # textposition='auto',  # Set the position of the labels
        ), layout=layout)

        config = {'displayModeBar': False}
        
        return fig.to_html(config=config)
    
    def build_grouped_horizontal_bar_chart(self, y, x1, x2):
        layout = go.Layout(
            # title='Double Line Chart',
            xaxis=dict(
                tickfont=dict(color='white'), 
                titlefont=dict(color='white'), 
                showgrid=True,
                domain=[0.5, 1],
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
            annotations=[
                dict(
                    xref='paper', 
                    yref='y',
                    x=0.5, 
                    y=yd,
                    xanchor='right',
                    text=str(yd),
                    font=dict(family='Arial', size=12, color='white'),
                    showarrow=False, 
                    align='right'
                ) for yd in y
            ],
            barmode="group"
        )

        # Create the bar chart using plotly
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=x1,  # Use values as the x-axis values
            y=y,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={"color": ["#71EDF1" for _ in y]},
            # texttemplate='%{y}',  # Use %{y} to display the category names as labels
            # textposition='auto',  # Set the position of the labels
        ))

        fig.add_trace(go.Bar(
            x=x2,  # Use values as the x-axis values
            y=y,  # Use categories as the y-axis values
            yperiodalignment="middle",
            orientation='h',  # Set the orientation to horizontal
            marker={"color": ["#71EDF1" for _ in y]},
            # texttemplate='%{y}',  # Use %{y} to display the category names as labels
            # textposition='auto',  # Set the position of the labels
        ))

        fig.update_layout(layout)

        config = {'displayModeBar': False}
        
        return fig.to_html(config=config)
    
    def build_year_to_year_line_chart(self, x, y1, y2, label1, label2, upper_limit):
        # Create the first line chart trace
        trace1 = go.Scatter(
            x=x,
            y=y1,
            mode='lines',
            name=label1,
            line=dict(color="#46A1BF")
        )

        # Create the second line chart trace
        trace2 = go.Scatter(
            x=x,
            y=y2,
            mode='lines',
            name=label2,
            line=dict(color="#5cc4cc")
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
            height=180,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(x=0.5, y=1.1, orientation='h', yanchor='top', xanchor='center', font=dict(color="white")),
            margin=dict(l=1, r=1, b=1, t=1, pad=1),
        )

        # Create the chart object
        fig = go.Figure(data=data, layout=layout)
        config = {'displayModeBar': False}

        return fig.to_html(config=config)  
