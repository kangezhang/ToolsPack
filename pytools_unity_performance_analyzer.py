# ==== run_performance_analyzer.py ====
"""
Unity性能数据可视化分析工具 - 稳定版本
完全修复所有Plotly配置错误
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
from datetime import datetime
import io


class PerformanceAnalyzerGUI:

    def __init__(self):
        self.df = None
        self.setup_page()

    def setup_page(self):
        st.set_page_config(
            page_title="Unity性能分析工具",
            page_icon="■",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        st.markdown("""
            <style>
            .stApp {
                background-color: #FFFFFF;
                color: #000000;
            }
            .stMarkdown {
                color: #000000;
                font-size: 15px;
            }
            .stMetric {
                background-color: #F8F9FA;
                padding: 18px;
                border-radius: 6px;
                border: 1px solid #DEE2E6;
            }
            .stMetric label {
                color: #000000 !important;
                font-weight: 600 !important;
                font-size: 16px !important;
            }
            .stMetric [data-testid="stMetricValue"] {
                color: #000000 !important;
                font-weight: 700 !important;
                font-size: 28px !important;
            }
            .stMetric [data-testid="stMetricDelta"] {
                font-size: 14px !important;
            }
            .stAlert {
                background-color: #F8F9FA;
                color: #000000;
                border: 1px solid #DEE2E6;
                font-size: 15px;
            }
            h1 {
                color: #000000 !important;
                font-size: 36px !important;
                font-weight: 700 !important;
            }
            h2 {
                color: #000000 !important;
                font-size: 28px !important;
                font-weight: 600 !important;
            }
            h3 {
                color: #000000 !important;
                font-size: 22px !important;
                font-weight: 600 !important;
            }
            .stDataFrame {
                background-color: #FFFFFF !important;
                font-size: 15px !important;
            }
            .stDataFrame thead tr th {
                background-color: #F1F3F5 !important;
                color: #000000 !important;
                font-weight: 700 !important;
                border: 1px solid #DEE2E6 !important;
                padding: 14px 12px !important;
                font-size: 15px !important;
            }
            .stDataFrame tbody tr td {
                background-color: #FFFFFF !important;
                color: #000000 !important;
                border: 1px solid #E9ECEF !important;
                padding: 12px !important;
                font-size: 15px !important;
            }
            .stDataFrame tbody tr:hover td {
                background-color: #F8F9FA !important;
            }
            .stButton button {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #DEE2E6;
                font-size: 15px;
                font-weight: 500;
            }
            .stButton button:hover {
                background-color: #F8F9FA;
                border: 1px solid #ADB5BD;
            }
            .stTabs [data-baseweb="tab"] {
                font-size: 16px;
                font-weight: 500;
                color: #000000;
                padding: 12px 24px;
            }
            </style>
        """, unsafe_allow_html=True)

        st.title("Unity性能数据可视化分析工具")
        st.markdown("---")

    def load_data_section(self):
        st.sidebar.header("数据加载")

        uploaded_file = st.sidebar.file_uploader(
            "上传CSV文件",
            type=['csv'],
            help="上传Unity PerformanceMonitor生成的CSV文件"
        )

        if uploaded_file is not None:
            try:
                self.df = pd.read_csv(uploaded_file)
                st.sidebar.success(f"成功加载 {len(self.df)} 条记录")

                st.sidebar.metric("数据点数", f"{len(self.df):,}")
                st.sidebar.metric("时间跨度",
                                  f"{self.df['时间戳'].max() - self.df['时间戳'].min():.1f}秒")
                st.sidebar.metric("异常帧数",
                                  f"{len(self.df[self.df['是否异常'] == '是']):,}")

                return True
            except Exception as e:
                st.sidebar.error(f"加载失败: {e}")
                return False

        if st.sidebar.button("使用演示数据"):
            self.df = self.generate_demo_data()
            st.sidebar.success("演示数据已加载")
            return True

        return False

    def generate_demo_data(self):
        np.random.seed(42)
        n = 500

        timestamps = np.linspace(0, 250, n)
        fps = 60 + np.random.randn(n) * 5
        fps[100:120] = 25 + np.random.randn(20) * 3
        fps[300:310] = 20 + np.random.randn(10) * 2
        fps = np.clip(fps, 10, 120)

        memory = 200 + timestamps * 0.5 + np.random.randn(n) * 10
        memory = np.clip(memory, 150, 500)

        gc_rate = np.abs(np.random.randn(n) * 3)
        gc_rate[100:120] = 15 + np.random.randn(20) * 2
        gc_rate[300:310] = 20 + np.random.randn(10) * 3

        df = pd.DataFrame({
            '时间戳': timestamps,
            'FPS': fps,
            '帧时间': 1 / fps,
            '总内存(MB)': memory,
            'Mono内存(MB)': memory * 0.6,
            'GC内存(MB)': memory * 0.3,
            'GC分配率(MB/s)': gc_rate,
            'DrawCalls': np.random.randint(300, 1200, n),
            'Batches': np.random.randint(50, 200, n),
            '三角形': np.random.randint(10000, 50000, n),
            '顶点': np.random.randint(5000, 25000, n),
            '是否异常': ['否'] * n,
            '异常原因': [''] * n
        })

        anomaly_mask = (df['FPS'] < 30) | (df['GC分配率(MB/s)'] > 10)
        df.loc[anomaly_mask, '是否异常'] = '是'
        df.loc[anomaly_mask, '异常原因'] = 'FPS过低或GC过高'

        return df

    def overview_section(self):
        st.header("性能概览")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            avg_fps = self.df['FPS'].mean()
            st.metric("平均FPS", f"{avg_fps:.1f}", delta=f"{avg_fps - 60:.1f}")

        with col2:
            min_fps = self.df['FPS'].min()
            st.metric("最低FPS", f"{min_fps:.1f}",
                      delta=f"{min_fps - 30:.1f}" if min_fps < 30 else None,
                      delta_color="inverse")

        with col3:
            avg_memory = self.df['总内存(MB)'].mean()
            st.metric("平均内存", f"{avg_memory:.0f}MB")

        with col4:
            max_gc = self.df['GC分配率(MB/s)'].max()
            st.metric("最大GC", f"{max_gc:.2f}MB/s",
                      delta="警告" if max_gc > 10 else "正常",
                      delta_color="inverse" if max_gc > 10 else "normal")

        with col5:
            anomaly_rate = (len(self.df[self.df['是否异常'] == '是']) / len(self.df)) * 100
            st.metric("异常率", f"{anomaly_rate:.1f}%",
                      delta="高" if anomaly_rate > 10 else "低",
                      delta_color="inverse" if anomaly_rate > 10 else "normal")

    def fps_analysis_section(self):
        st.header("FPS分析")

        fig = go.Figure()

        normal_data = self.df[self.df['是否异常'] == '否']
        fig.add_trace(go.Scatter(
            x=normal_data['时间戳'],
            y=normal_data['FPS'],
            mode='lines',
            name='正常FPS',
            line=dict(color='#2C3E50', width=2),
            hovertemplate='时间: %{x:.2f}s<br>FPS: %{y:.1f}<extra></extra>'
        ))

        anomaly_data = self.df[self.df['是否异常'] == '是']
        if len(anomaly_data) > 0:
            fig.add_trace(go.Scatter(
                x=anomaly_data['时间戳'],
                y=anomaly_data['FPS'],
                mode='markers',
                name='异常帧',
                marker=dict(color='#E74C3C', size=10, symbol='x'),
                hovertemplate='时间: %{x:.2f}s<br>FPS: %{y:.1f}<extra></extra>'
            ))

        fig.add_hline(y=60, line_dash="dash", line_color="#27AE60", line_width=2,
                      annotation_text="理想FPS(60)", annotation_position="right")
        fig.add_hline(y=30, line_dash="dash", line_color="#F39C12", line_width=2,
                      annotation_text="低FPS阈值(30)", annotation_position="right")

        fig.update_layout(
            title="FPS时间线",
            xaxis_title="时间 (秒)",
            yaxis_title="FPS",
            height=500,
            template='plotly_white',
            font=dict(size=14, color='black'),
            title_font=dict(size=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=self.df['FPS'],
                nbinsx=50,
                marker_color='#34495E'
            ))
            fig_hist.update_layout(
                title="FPS分布直方图",
                xaxis_title="FPS",
                yaxis_title="频次",
                height=350,
                template='plotly_white',
                font=dict(size=14, color='black'),
                title_font=dict(size=18)
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            st.subheader("统计信息")
            stats_df = pd.DataFrame({
                '指标': ['平均值', '中位数', '最小值', '最大值', '标准差'],
                '数值': [
                    f"{self.df['FPS'].mean():.2f}",
                    f"{self.df['FPS'].median():.2f}",
                    f"{self.df['FPS'].min():.2f}",
                    f"{self.df['FPS'].max():.2f}",
                    f"{self.df['FPS'].std():.2f}"
                ]
            })
            st.dataframe(stats_df, hide_index=True, use_container_width=True, height=245)

    def memory_analysis_section(self):
        st.header("内存分析")

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("内存使用趋势", "GC分配率"),
            vertical_spacing=0.12,
            row_heights=[0.6, 0.4]
        )

        fig.add_trace(
            go.Scatter(x=self.df['时间戳'], y=self.df['总内存(MB)'],
                       name='总内存', line=dict(color='#E74C3C', width=2.5)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.df['时间戳'], y=self.df['Mono内存(MB)'],
                       name='Mono内存', line=dict(color='#3498DB', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.df['时间戳'], y=self.df['GC内存(MB)'],
                       name='GC内存', line=dict(color='#9B59B6', width=2)),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=self.df['时间戳'], y=self.df['GC分配率(MB/s)'],
                       name='GC分配率', fill='tozeroy',
                       line=dict(color='#F39C12', width=2)),
            row=2, col=1
        )

        high_gc = self.df[self.df['GC分配率(MB/s)'] > 10]
        if len(high_gc) > 0:
            fig.add_trace(
                go.Scatter(x=high_gc['时间戳'], y=high_gc['GC分配率(MB/s)'],
                           mode='markers', name='高GC(>10MB/s)',
                           marker=dict(color='#C0392B', size=10, symbol='diamond')),
                row=2, col=1
            )

        fig.update_xaxes(title_text="时间 (秒)", row=2, col=1)
        fig.update_yaxes(title_text="内存 (MB)", row=1, col=1)
        fig.update_yaxes(title_text="GC (MB/s)", row=2, col=1)

        fig.update_layout(
            height=700,
            template='plotly_white',
            font=dict(size=14, color='black')
        )

        st.plotly_chart(fig, use_container_width=True)

        memory_trend = np.polyfit(range(len(self.df)), self.df['总内存(MB)'], 1)
        memory_slope = memory_trend[0]

        if memory_slope > 0.1:
            st.warning(f"检测到内存持续增长趋势: +{memory_slope:.2f}MB/采样")
            st.info("建议检查是否存在内存泄漏，关注未释放的对象引用")
        else:
            st.success("内存使用稳定，未检测到明显泄漏")

    def gc_analysis_section(self):
        st.header("GC分析")

        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                self.df,
                x='GC分配率(MB/s)',
                nbins=50,
                title="GC分配率分布",
                color_discrete_sequence=['#8E44AD']
            )
            fig.add_vline(
                x=self.df['GC分配率(MB/s)'].mean(),
                line_dash="dash",
                line_color="#E74C3C",
                line_width=2,
                annotation_text="平均值"
            )
            fig.update_layout(
                xaxis_title="GC分配率 (MB/s)",
                yaxis_title="频次",
                height=400,
                template='plotly_white',
                font=dict(size=14, color='black'),
                title_font=dict(size=18)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                self.df,
                x='GC分配率(MB/s)',
                y='FPS',
                color='时间戳',
                title="GC分配率 vs FPS相关性",
                color_continuous_scale='Greys'
            )
            fig.update_layout(
                xaxis_title="GC分配率 (MB/s)",
                yaxis_title="FPS",
                height=400,
                template='plotly_white',
                font=dict(size=14, color='black'),
                title_font=dict(size=18)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("GC统计")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("平均GC", f"{self.df['GC分配率(MB/s)'].mean():.2f} MB/s")
        with col2:
            st.metric("最大GC", f"{self.df['GC分配率(MB/s)'].max():.2f} MB/s")
        with col3:
            high_gc_count = len(self.df[self.df['GC分配率(MB/s)'] > 10])
            st.metric("高GC次数", f"{high_gc_count:,}")
        with col4:
            total_gc = self.df['GC分配率(MB/s)'].sum()
            st.metric("总GC分配", f"{total_gc:.2f} MB")

    def rendering_analysis_section(self):
        st.header("渲染分析")

        if 'DrawCalls' in self.df.columns and self.df['DrawCalls'].sum() > 0:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("DrawCalls", "Batches", "三角形数", "顶点数")
            )

            metrics = [
                ('DrawCalls', 1, 1, '#E74C3C'),
                ('Batches', 1, 2, '#3498DB'),
                ('三角形', 2, 1, '#2ECC71'),
                ('顶点', 2, 2, '#F39C12')
            ]

            for metric, row, col, color in metrics:
                if metric in self.df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=self.df['时间戳'],
                            y=self.df[metric],
                            name=metric,
                            line=dict(color=color, width=2),
                            showlegend=False
                        ),
                        row=row, col=col
                    )

            fig.update_xaxes(title_text="时间 (秒)")
            fig.update_layout(
                height=600,
                template='plotly_white',
                font=dict(size=14, color='black')
            )

            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("平均DrawCalls", f"{self.df['DrawCalls'].mean():.0f}")
            with col2:
                st.metric("平均Batches", f"{self.df.get('Batches', pd.Series([0])).mean():.0f}")
            with col3:
                st.metric("平均三角形", f"{self.df.get('三角形', pd.Series([0])).mean():,.0f}")
            with col4:
                st.metric("平均顶点", f"{self.df.get('顶点', pd.Series([0])).mean():,.0f}")
        else:
            st.info("CSV文件中未包含渲染统计数据")

    def anomaly_section(self):
        st.header("异常分析")

        anomalies = self.df[self.df['是否异常'] == '是']

        if len(anomalies) == 0:
            st.success("未检测到性能异常")
            return

        st.warning(f"检测到 {len(anomalies):,} 个异常帧")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=self.df['时间戳'],
            y=self.df['FPS'],
            mode='lines',
            name='FPS',
            line=dict(color='#BDC3C7', width=1.5)
        ))

        fig.add_trace(go.Scatter(
            x=anomalies['时间戳'],
            y=anomalies['FPS'],
            mode='markers',
            name='异常点',
            marker=dict(
                size=14,
                color=anomalies['时间戳'],
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="时间")
            )
        ))

        fig.update_layout(
            title="异常分布时间线",
            xaxis_title="时间 (秒)",
            yaxis_title="FPS",
            height=400,
            template='plotly_white',
            font=dict(size=14, color='black'),
            title_font=dict(size=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("最严重的异常帧 TOP10")
        worst_anomalies = anomalies.nsmallest(10, 'FPS')[[
            '时间戳', 'FPS', '总内存(MB)', 'GC分配率(MB/s)', '异常原因'
        ]].copy()
        worst_anomalies.columns = ['时间(秒)', 'FPS', '内存(MB)', 'GC(MB/s)', '原因']
        worst_anomalies['时间(秒)'] = worst_anomalies['时间(秒)'].round(2)
        worst_anomalies['FPS'] = worst_anomalies['FPS'].round(1)
        worst_anomalies['内存(MB)'] = worst_anomalies['内存(MB)'].round(1)
        worst_anomalies['GC(MB/s)'] = worst_anomalies['GC(MB/s)'].round(2)

        st.dataframe(worst_anomalies, hide_index=True, use_container_width=True, height=420)

    def correlation_section(self):
        st.header("指标相关性分析")

        numeric_cols = ['FPS', '帧时间', '总内存(MB)', 'Mono内存(MB)',
                        'GC内存(MB)', 'GC分配率(MB/s)']

        if 'DrawCalls' in self.df.columns and self.df['DrawCalls'].sum() > 0:
            numeric_cols.append('DrawCalls')

        correlation = self.df[numeric_cols].corr()

        fig = go.Figure(data=go.Heatmap(
            z=correlation.values,
            x=correlation.columns,
            y=correlation.columns,
            colorscale='RdBu',
            zmid=0,
            text=correlation.values.round(2),
            texttemplate='%{text}',
            textfont=dict(size=16, color="black"),
            colorbar=dict(title="相关系数")
        ))

        fig.update_layout(
            title="性能指标相关性热图",
            height=650,
            template='plotly_white',
            font=dict(size=15, color='black'),
            title_font=dict(size=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("相关性解读")

        strong_correlations = []
        for i in range(len(correlation.columns)):
            for j in range(i + 1, len(correlation.columns)):
                corr_value = correlation.iloc[i, j]
                if abs(corr_value) > 0.6:
                    strong_correlations.append({
                        '指标1': correlation.columns[i],
                        '指标2': correlation.columns[j],
                        '相关系数': f"{corr_value:.2f}",
                        '关系': '强正相关' if corr_value > 0 else '强负相关'
                    })

        if strong_correlations:
            df_corr = pd.DataFrame(strong_correlations)
            st.dataframe(df_corr, hide_index=True, use_container_width=True)
        else:
            st.info("未发现显著的强相关关系")

    def export_section(self):
        st.sidebar.markdown("---")
        st.sidebar.header("导出功能")

        if st.sidebar.button("生成分析报告"):
            report = self.generate_text_report()
            st.sidebar.download_button(
                label="下载分析报告",
                data=report,
                file_name=f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

        if st.sidebar.button("导出CSV数据"):
            csv = self.df.to_csv(index=False)
            st.sidebar.download_button(
                label="下载CSV文件",
                data=csv,
                file_name=f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    def generate_text_report(self):
        report = io.StringIO()

        report.write("=" * 60 + "\n")
        report.write("Unity性能分析报告\n")
        report.write("=" * 60 + "\n")
        report.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.write(f"数据点数: {len(self.df):,}\n")
        report.write(f"时间跨度: {self.df['时间戳'].max() - self.df['时间戳'].min():.1f}秒\n\n")

        report.write("统计摘要\n")
        report.write("-" * 60 + "\n")
        report.write(f"FPS - 平均: {self.df['FPS'].mean():.1f}, ")
        report.write(f"最小: {self.df['FPS'].min():.1f}, ")
        report.write(f"最大: {self.df['FPS'].max():.1f}\n")

        report.write(f"内存(MB) - 平均: {self.df['总内存(MB)'].mean():.1f}, ")
        report.write(f"最小: {self.df['总内存(MB)'].min():.1f}, ")
        report.write(f"最大: {self.df['总内存(MB)'].max():.1f}\n")

        report.write(f"GC(MB/s) - 平均: {self.df['GC分配率(MB/s)'].mean():.2f}, ")
        report.write(f"最大: {self.df['GC分配率(MB/s)'].max():.2f}\n\n")

        anomaly_count = len(self.df[self.df['是否异常'] == '是'])
        report.write(f"异常帧数: {anomaly_count:,} ")
        report.write(f"({anomaly_count / len(self.df) * 100:.1f}%)\n")

        return report.getvalue()

    def run(self):
        if not self.load_data_section():
            st.info("请在左侧上传CSV文件或使用演示数据开始分析")

            st.markdown("""
            ### 使用说明

            1. 上传数据: 点击左侧上传CSV文件
            2. 查看分析: 自动生成多维度可视化图表
            3. 导出报告: 可在左侧导出详细分析报告

            ### 主要功能

            - 性能概览: 关键指标一览
            - FPS分析: 时间线、分布统计
            - 内存分析: 趋势、GC分析、泄漏检测
            - GC分析: 分配率分布与相关性
            - 渲染分析: DrawCall、Batch统计
            - 异常分析: 异常检测与定位
            - 相关性分析: 指标间关联关系
            """)
            return

        self.overview_section()
        st.markdown("---")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "FPS分析",
            "内存与GC",
            "渲染分析",
            "异常分析",
            "相关性分析"
        ])

        with tab1:
            self.fps_analysis_section()

        with tab2:
            self.memory_analysis_section()
            st.markdown("---")
            self.gc_analysis_section()

        with tab3:
            self.rendering_analysis_section()

        with tab4:
            self.anomaly_section()

        with tab5:
            self.correlation_section()

        self.export_section()


if __name__ == '__main__':
    app = PerformanceAnalyzerGUI()
    app.run()