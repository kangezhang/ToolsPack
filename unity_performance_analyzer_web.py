#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity性能数据交互式可视化分析工具
功能完整版 - 类似Streamlit效果
"""

import pandas as pd
import numpy as np
import json
import webbrowser
import os
from pathlib import Path
from datetime import datetime


class InteractivePerformanceAnalyzer:
    """交互式性能分析器"""

    def __init__(self, csv_file, platform='PC'):
        self.csv_file = csv_file
        self.platform = platform
        self.df = None
        self.results = {}

    def load_data(self):
        """加载CSV数据"""
        print(f"正在加载数据: {self.csv_file}")
        self.df = pd.read_csv(self.csv_file)

        print(f"✓ 加载完成: {len(self.df)} 条记录")
        print(f"✓ 检测到列: {list(self.df.columns)}")

        # 数据清洗
        if 'FPS' in self.df.columns:
            self.df = self.df[self.df['FPS'] > 0]
            self.df = self.df[self.df['FPS'] < 1000]
            print(f"✓ 清洗后记录数: {len(self.df)}")
        else:
            print("⚠ 警告: 未找到FPS列")

    def analyze(self):
        """执行完整分析"""
        print("正在分析数据...")

        self.results = {
            'metadata': self._analyze_metadata(),
            'summary': self._analyze_summary(),
            'fps': self._analyze_fps(),
            'memory': self._analyze_memory(),
            'gc': self._analyze_gc(),
            'rendering': self._analyze_rendering(),
            'cpu': self._analyze_cpu(),
            'anomalies': self._analyze_anomalies(),
            'scenes': self._analyze_scenes(),
            'correlations': self._analyze_correlations(),
            'trends': self._analyze_trends(),
            'bottleneck': self._analyze_bottleneck(),
            'mobile_predictions': None,
            'chart_data': self._prepare_chart_data()
        }

        if self.platform != 'PC':
            self.results['mobile_predictions'] = self._predict_mobile()

        self.results['performance_score'] = self._calculate_score()
        self.results['issues'] = self._detect_issues()
        self.results['recommendations'] = self._generate_recommendations()

        print("✓ 分析完成")

    def _analyze_metadata(self):
        """元数据分析"""
        return {
            'file_name': os.path.basename(self.csv_file),
            'platform': self.platform,
            'record_count': len(self.df),
            'columns': list(self.df.columns)
        }

    def _analyze_summary(self):
        """汇总统计"""
        duration = 0
        if 'Timestamp' in self.df.columns and len(self.df) > 1:
            duration = self.df['Timestamp'].iloc[-1] - self.df['Timestamp'].iloc[0]

        return {
            'duration_seconds': float(duration),
            'duration_minutes': float(duration / 60) if duration > 0 else 0,
            'total_samples': len(self.df),
            'sample_rate': float(duration / len(self.df)) if len(self.df) > 1 else 0.5
        }

    def _analyze_fps(self):
        """FPS分析"""
        if 'FPS' not in self.df.columns:
            return {'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'std': 0, 'cv': 0,
                    'p1': 0, 'p5': 0, 'p25': 0, 'p75': 0, 'p95': 0, 'p99': 0}

        fps = self.df['FPS']
        return {
            'mean': float(fps.mean()),
            'median': float(fps.median()),
            'min': float(fps.min()),
            'max': float(fps.max()),
            'std': float(fps.std()),
            'cv': float(fps.std() / fps.mean()) if fps.mean() > 0 else 0,
            'p1': float(fps.quantile(0.01)),
            'p5': float(fps.quantile(0.05)),
            'p25': float(fps.quantile(0.25)),
            'p75': float(fps.quantile(0.75)),
            'p95': float(fps.quantile(0.95)),
            'p99': float(fps.quantile(0.99))
        }

    def _analyze_memory(self):
        """内存分析"""
        if 'TotalAllocated_MB' not in self.df.columns:
            return {}

        mem = self.df['TotalAllocated_MB']
        duration = 1
        if 'Timestamp' in self.df.columns and len(self.df) > 1:
            duration = max(1, self.df['Timestamp'].iloc[-1] - self.df['Timestamp'].iloc[0])

        return {
            'mean': float(mem.mean()),
            'min': float(mem.min()),
            'max': float(mem.max()),
            'growth': float(mem.iloc[-1] - mem.iloc[0]),
            'growth_rate': float((mem.iloc[-1] - mem.iloc[0]) / duration)
        }

    def _analyze_gc(self):
        """GC分析"""
        if 'GCAllocThisFrame_KB' not in self.df.columns:
            return {}

        gc = self.df['GCAllocThisFrame_KB']
        return {
            'mean': float(gc.mean()),
            'median': float(gc.median()),
            'max': float(gc.max()),
            'total': float(gc.sum()),
            'spike_count': int((gc > 500).sum()),
            'spike_rate': float((gc > 500).sum() / len(gc)) if len(gc) > 0 else 0
        }

    def _analyze_rendering(self):
        """渲染分析"""
        result = {}
        if 'DrawCalls' in self.df.columns:
            result['draw_calls_mean'] = float(self.df['DrawCalls'].mean())
            result['draw_calls_max'] = float(self.df['DrawCalls'].max())
        if 'Triangles' in self.df.columns:
            result['triangles_mean'] = float(self.df['Triangles'].mean())
        return result

    def _analyze_cpu(self):
        """CPU分析"""
        if 'CPUFrameTime_ms' not in self.df.columns:
            return {}

        cpu = self.df['CPUFrameTime_ms']
        return {
            'mean': float(cpu.mean()),
            'median': float(cpu.median()),
            'max': float(cpu.max()),
            'p95': float(cpu.quantile(0.95)),
            'p99': float(cpu.quantile(0.99))
        }

    def _analyze_anomalies(self):
        """异常分析 - 增强版"""
        anomaly_count = 0

        # 尝试多种可能的列名
        possible_columns = ['IsAnomaly', '是否异常', 'Anomaly', 'isAnomaly']
        anomaly_column = None

        for col in possible_columns:
            if col in self.df.columns:
                anomaly_column = col
                break

        if anomaly_column:
            # 处理不同的数据类型
            if self.df[anomaly_column].dtype == bool:
                anomaly_count = int(self.df[anomaly_column].sum())
            elif self.df[anomaly_column].dtype in ['int64', 'int32']:
                anomaly_count = int((self.df[anomaly_column] == 1).sum())
            else:
                # 字符串类型：'是', 'True', '1'等
                anomaly_count = int(self.df[anomaly_column].isin(['是', 'True', '1', 1, True]).sum())
        else:
            # 如果没有异常列，基于FPS自动判断
            if 'FPS' in self.df.columns:
                # FPS < 30 或者突降超过20 FPS
                fps = self.df['FPS']
                low_fps = fps < 30

                # 计算FPS骤降
                fps_drop = fps.diff() < -20

                anomaly_count = int((low_fps | fps_drop).sum())
                print(f"⚠ 未找到异常标记列，基于FPS自动检测到 {anomaly_count} 个异常帧")

        return {
            'count': anomaly_count,
            'rate': float(anomaly_count / len(self.df)) if len(self.df) > 0 else 0,
            'detection_method': 'manual' if anomaly_column else 'auto'
        }

    def _analyze_scenes(self):
        """场景分析"""
        if 'CurrentSceneName' not in self.df.columns:
            return {}

        scenes = {}
        for scene in self.df['CurrentSceneName'].unique():
            if pd.isna(scene):
                continue
            scene_data = self.df[self.df['CurrentSceneName'] == scene]
            if 'FPS' in scene_data.columns:
                scenes[scene] = {
                    'count': len(scene_data),
                    'avg_fps': float(scene_data['FPS'].mean())
                }
        return scenes

    def _analyze_correlations(self):
        """相关性分析"""
        numeric_cols = ['FPS']
        for col in ['TotalAllocated_MB', 'GCAllocThisFrame_KB', 'DrawCalls', 'CPUFrameTime_ms']:
            if col in self.df.columns:
                numeric_cols.append(col)

        if len(numeric_cols) < 2:
            return {}

        corr_matrix = self.df[numeric_cols].corr()
        return corr_matrix.to_dict()

    def _analyze_trends(self):
        """趋势分析"""
        results = {}

        if 'FPS' in self.df.columns:
            fps_data = self.df['FPS'].values
            results['fps'] = self._analyze_single_trend(fps_data)

        if 'TotalAllocated_MB' in self.df.columns:
            mem_data = self.df['TotalAllocated_MB'].values
            results['memory'] = self._analyze_single_trend(mem_data)

        return results

    def _analyze_single_trend(self, data):
        """单个指标趋势"""
        if len(data) < 2:
            return {'slope': 0, 'trend_type': 'stable'}

        x = np.arange(len(data))
        slope = float(np.polyfit(x, data, 1)[0])

        if abs(slope) < 0.001:
            trend_type = 'stable'
        elif slope > 0:
            trend_type = 'increasing'
        else:
            trend_type = 'decreasing'

        return {'slope': slope, 'trend_type': trend_type}

    def _analyze_bottleneck(self):
        """瓶颈分析"""
        if 'CPUFrameTime_ms' not in self.df.columns:
            return {}

        gpu_col = None
        for col in ['GPUFrameTime_ms', 'GPU_ms', 'GPUTime_ms']:
            if col in self.df.columns:
                gpu_col = col
                break

        if gpu_col is None:
            return {}

        cpu_time = self.df['CPUFrameTime_ms'].values
        gpu_time = self.df[gpu_col].values

        cpu_bottleneck = np.sum(cpu_time > gpu_time)
        gpu_bottleneck = np.sum(gpu_time > cpu_time)
        total = len(cpu_time)

        return {
            'cpu_bottleneck_rate': float(cpu_bottleneck / total),
            'gpu_bottleneck_rate': float(gpu_bottleneck / total),
            'dominant_bottleneck': 'CPU' if cpu_bottleneck > gpu_bottleneck else 'GPU' if gpu_bottleneck > cpu_bottleneck else 'Balanced'
        }

    def _predict_mobile(self):
        """移动平台预测"""
        devices = {
            'flagship_2024': {'name': '2024旗舰机', 'fps_ratio': 0.90, 'memory_ratio': 1.15},
            'flagship_2022': {'name': '2022旗舰机', 'fps_ratio': 0.80, 'memory_ratio': 1.30},
            'high_end': {'name': '高端设备', 'fps_ratio': 0.65, 'memory_ratio': 1.60},
            'mid_range': {'name': '中端设备', 'fps_ratio': 0.50, 'memory_ratio': 2.00},
            'low_end': {'name': '低端设备', 'fps_ratio': 0.35, 'memory_ratio': 2.80}
        }

        base_fps = self.results.get('fps', {}).get('mean', 60)
        base_memory = self.results.get('memory', {}).get('max', 512)

        predictions = {}
        for key, device in devices.items():
            pred_fps = base_fps * device['fps_ratio']
            pred_memory = base_memory * device['memory_ratio']

            predictions[key] = {
                'name': device['name'],
                'predicted_fps': float(pred_fps),
                'predicted_memory': float(pred_memory),
                'playable': bool(pred_fps >= 30)
            }

        return predictions

    def _calculate_score(self):
        """计算性能评分"""
        score = 100
        fps = self.results.get('fps', {})
        mem = self.results.get('memory', {})
        gc = self.results.get('gc', {})

        if fps.get('mean', 60) < 60:
            score -= (60 - fps.get('mean', 60)) * 0.5

        if mem.get('max', 0) > 800:
            score -= (mem.get('max', 0) - 800) * 0.05

        if gc.get('mean', 0) > 100:
            score -= (gc.get('mean', 0) - 100) * 0.1

        return max(0, min(100, float(score)))

    def _detect_issues(self):
        """检测问题"""
        issues = []
        fps = self.results.get('fps', {})

        if fps.get('mean', 60) < 30:
            issues.append({
                'severity': 'critical',
                'category': 'FPS',
                'description': f"平均FPS过低 ({fps.get('mean', 0):.1f})",
                'suggestion': '检查CPU/GPU瓶颈，优化渲染管线'
            })

        mem = self.results.get('memory', {})
        if mem.get('max', 0) > 800:
            issues.append({
                'severity': 'critical',
                'category': 'Memory',
                'description': f"内存峰值过高 ({mem.get('max', 0):.0f}MB)",
                'suggestion': '检查纹理压缩、对象池使用'
            })

        gc = self.results.get('gc', {})
        if gc.get('mean', 0) > 100:
            issues.append({
                'severity': 'warning',
                'category': 'GC',
                'description': f"GC压力过大 ({gc.get('mean', 0):.0f}KB/帧)",
                'suggestion': '减少装箱、字符串拼接，使用对象池'
            })

        return issues

    def _generate_recommendations(self):
        """生成建议"""
        recommendations = []
        issues = self.results.get('issues', [])

        if any(i['category'] == 'FPS' for i in issues):
            recommendations.append({
                'category': '帧率优化',
                'priority': 'high',
                'suggestions': [
                    '使用Unity Profiler深度分析CPU/GPU时间分布',
                    '检查Update/FixedUpdate中的重度计算',
                    '优化物理计算：降低Fixed Timestep'
                ]
            })

        if any(i['category'] == 'GC' for i in issues):
            recommendations.append({
                'category': 'GC优化',
                'priority': 'high',
                'suggestions': [
                    '使用对象池管理频繁创建/销毁的对象',
                    '避免在Update中使用string拼接',
                    '减少LINQ查询，替换为for循环'
                ]
            })

        return recommendations

    def _prepare_chart_data(self):
        """准备图表数据 - 增强版"""
        chart_data = {}

        # 时间轴
        if 'Timestamp' in self.df.columns:
            timestamps = self.df['Timestamp'].tolist()
        else:
            timestamps = list(range(len(self.df)))

        chart_data['timestamps'] = timestamps

        # FPS数据
        if 'FPS' in self.df.columns:
            chart_data['fps'] = self.df['FPS'].tolist()
            chart_data['fps_anomaly'] = []

            # 尝试多种异常列名
            anomaly_col = None
            for col in ['IsAnomaly', '是否异常', 'Anomaly']:
                if col in self.df.columns:
                    anomaly_col = col
                    break

            if anomaly_col:
                # 根据数据类型过滤异常
                if self.df[anomaly_col].dtype == bool:
                    anomalies = self.df[self.df[anomaly_col] == True]
                elif self.df[anomaly_col].dtype in ['int64', 'int32']:
                    anomalies = self.df[self.df[anomaly_col] == 1]
                else:
                    anomalies = self.df[self.df[anomaly_col].isin(['是', 'True', '1', 1, True])]

                chart_data['fps_anomaly'] = [
                    {'x': float(row['Timestamp']) if 'Timestamp' in self.df.columns else i,
                     'y': float(row['FPS'])}
                    for i, row in anomalies.iterrows()
                ]
            else:
                # 自动检测异常：FPS < 30 或骤降 > 20
                fps = self.df['FPS']
                anomaly_mask = (fps < 30) | (fps.diff() < -20)
                anomalies = self.df[anomaly_mask]

                chart_data['fps_anomaly'] = [
                    {'x': float(row['Timestamp']) if 'Timestamp' in self.df.columns else i,
                     'y': float(row['FPS'])}
                    for i, row in anomalies.iterrows()
                ]

        # 内存数据
        if 'TotalAllocated_MB' in self.df.columns:
            chart_data['memory_total'] = self.df['TotalAllocated_MB'].tolist()
        if 'MonoUsed_MB' in self.df.columns:
            chart_data['memory_mono'] = self.df['MonoUsed_MB'].tolist()

        # GC数据
        if 'GCAllocThisFrame_KB' in self.df.columns:
            chart_data['gc_alloc'] = self.df['GCAllocThisFrame_KB'].tolist()

        # CPU/GPU数据
        if 'CPUFrameTime_ms' in self.df.columns:
            chart_data['cpu_time'] = self.df['CPUFrameTime_ms'].tolist()

        for col in ['GPUFrameTime_ms', 'GPU_ms']:
            if col in self.df.columns:
                chart_data['gpu_time'] = self.df[col].tolist()
                break

        # 渲染数据
        if 'DrawCalls' in self.df.columns:
            chart_data['draw_calls'] = self.df['DrawCalls'].tolist()

        return chart_data

    def generate_interactive_html(self, output_file='performance_report.html'):
        """生成交互式HTML报告"""
        html_content = self._build_html_template()

        output_dir = Path('performance_analysis')
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ 交互式报告已生成: {output_path}")

        # 自动打开浏览器
        webbrowser.open(f'file://{output_path.absolute()}')
        print("✓ 正在打开浏览器...")

        return str(output_path)

    def _build_html_template(self):
        """构建HTML模板"""
        # 转换数据为JSON
        analysis_json = json.dumps(self.results, indent=2, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unity性能分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background: #F5F7FA;
            color: #2C3E50;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header-info {{
            opacity: 0.95;
            font-size: 1.1em;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.12);
        }}

        .metric-card.good {{
            border-left: 4px solid #27AE60;
        }}

        .metric-card.warning {{
            border-left: 4px solid #F39C12;
        }}

        .metric-card.bad {{
            border-left: 4px solid #E74C3C;
        }}

        .metric-title {{
            font-size: 0.9em;
            color: #7F8C8D;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        .metric-value {{
            font-size: 2.2em;
            font-weight: 700;
            color: #2C3E50;
            margin-bottom: 4px;
        }}

        .metric-label {{
            font-size: 0.85em;
            color: #95A5A6;
        }}

        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #E8E8E8;
            padding-bottom: 0;
        }}

        .tab {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px 8px 0 0;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            color: #7F8C8D;
            transition: all 0.3s;
        }}

        .tab:hover {{
            background: #F8F9FA;
            color: #2C3E50;
        }}

        .tab.active {{
            background: #667eea;
            color: white;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
            animation: fadeIn 0.4s;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .chart-section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }}

        .chart-section h2 {{
            color: #2C3E50;
            margin-bottom: 20px;
            font-size: 1.8em;
            padding-bottom: 12px;
            border-bottom: 3px solid #667eea;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin-top: 20px;
        }}

        .chart-container.large {{
            height: 500px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .stat-item {{
            background: #F8F9FA;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-item-label {{
            font-size: 0.85em;
            color: #7F8C8D;
            margin-bottom: 6px;
        }}

        .stat-item-value {{
            font-size: 1.5em;
            font-weight: 700;
            color: #2C3E50;
        }}

        .issue-list {{
            margin-top: 20px;
        }}

        .issue-item {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .issue-item.critical {{
            border-left-color: #E74C3C;
            background: #FFEBEE;
        }}

        .issue-item.warning {{
            border-left-color: #F39C12;
            background: #FFF8E1;
        }}

        .issue-severity {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 700;
            margin-right: 10px;
        }}

        .issue-severity.critical {{
            background: #E74C3C;
            color: white;
        }}

        .issue-severity.warning {{
            background: #F39C12;
            color: white;
        }}

        .recommendation-card {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 12px;
            border-left: 5px solid #27AE60;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}

        .recommendation-card h3 {{
            color: #27AE60;
            margin-bottom: 15px;
        }}

        .recommendation-card ul {{
            margin-left: 20px;
        }}

        .recommendation-card li {{
            margin-bottom: 10px;
            color: #2C3E50;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: #7F8C8D;
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Unity性能分析报告</h1>
            <div class="header-info">
                <span>文件: {self.results['metadata']['file_name']}</span> | 
                <span>平台: {self.results['metadata']['platform']}</span> | 
                <span>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </div>

        <div class="metrics-grid" id="metricsGrid"></div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('overview')">性能概览</button>
            <button class="tab" onclick="switchTab('fps')">FPS分析</button>
            <button class="tab" onclick="switchTab('memory')">内存与GC</button>
            <button class="tab" onclick="switchTab('rendering')">渲染分析</button>
            <button class="tab" onclick="switchTab('issues')">问题与建议</button>
        </div>

        <div id="overview" class="tab-content active">
            <div class="chart-section">
                <h2>性能时间线</h2>
                <div class="chart-container large">
                    <canvas id="overviewChart"></canvas>
                </div>
            </div>
        </div>

        <div id="fps" class="tab-content">
            <div class="chart-section">
                <h2>FPS时间序列</h2>
                <div class="chart-container large">
                    <canvas id="fpsTimelineChart"></canvas>
                </div>
            </div>

            <div class="chart-section">
                <h2>FPS分布统计</h2>
                <div class="chart-container">
                    <canvas id="fpsDistributionChart"></canvas>
                </div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-item-label">平均FPS</div>
                        <div class="stat-item-value">{self.results['fps']['mean']:.1f}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">最低FPS</div>
                        <div class="stat-item-value">{self.results['fps']['min']:.1f}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">P1低点</div>
                        <div class="stat-item-value">{self.results['fps']['p1']:.1f}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">P5低点</div>
                        <div class="stat-item-value">{self.results['fps']['p5']:.1f}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">P95高点</div>
                        <div class="stat-item-value">{self.results['fps']['p95']:.1f}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">变异系数</div>
                        <div class="stat-item-value">{self.results['fps']['cv']:.2f}</div>
                    </div>
                </div>
            </div>
        </div>

        <div id="memory" class="tab-content">
            <div class="chart-section">
                <h2>内存使用趋势</h2>
                <div class="chart-container">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>

            <div class="chart-section">
                <h2>GC分配</h2>
                <div class="chart-container">
                    <canvas id="gcChart"></canvas>
                </div>
            </div>
        </div>

        <div id="rendering" class="tab-content">
            <div class="chart-section">
                <h2>CPU/GPU时间</h2>
                <div class="chart-container">
                    <canvas id="cpuGpuChart"></canvas>
                </div>
            </div>

            <div class="chart-section">
                <h2>Draw Calls</h2>
                <div class="chart-container">
                    <canvas id="drawCallsChart"></canvas>
                </div>
            </div>
        </div>

        <div id="issues" class="tab-content">
            <div class="chart-section">
                <h2>检测到的问题</h2>
                <div class="issue-list" id="issuesList"></div>
            </div>

            <div class="chart-section">
                <h2>优化建议</h2>
                <div id="recommendationsList"></div>
            </div>
        </div>

        <div class="footer">
            <p>Unity Performance Interactive Analyzer v2.0</p>
            <p>Powered by Chart.js & Python</p>
        </div>
    </div>

    <script>
        // 分析数据
        const analysisData = {analysis_json};

        // 切换标签
        function switchTab(tabName) {{
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }}

        // 渲染指标卡片
        function renderMetrics() {{
            const fps = analysisData.fps;
            const score = analysisData.performance_score;
            const anomalyRate = analysisData.anomalies.rate * 100;

            const metrics = [
                {{
                    title: '性能评分',
                    value: score.toFixed(0),
                    label: '/ 100',
                    status: score >= 80 ? 'good' : score >= 60 ? 'warning' : 'bad'
                }},
                {{
                    title: '平均FPS',
                    value: fps.mean.toFixed(1),
                    label: `最低: ${{fps.min.toFixed(1)}}`,
                    status: fps.mean >= 55 ? 'good' : fps.mean >= 30 ? 'warning' : 'bad'
                }},
                {{
                    title: 'P1低点',
                    value: fps.p1.toFixed(1),
                    label: 'FPS',
                    status: fps.p1 >= 30 ? 'good' : fps.p1 >= 20 ? 'warning' : 'bad'
                }},
                {{
                    title: 'FPS稳定性',
                    value: (fps.cv * 100).toFixed(1),
                    label: '%变异系数',
                    status: fps.cv < 0.15 ? 'good' : fps.cv < 0.25 ? 'warning' : 'bad'
                }},
                {{
                    title: '异常率',
                    value: anomalyRate.toFixed(1),
                    label: `% (${{analysisData.anomalies.count}}次)`,
                    status: anomalyRate < 5 ? 'good' : anomalyRate < 15 ? 'warning' : 'bad'
                }}
            ];

            if (analysisData.memory && analysisData.memory.max) {{
                metrics.push({{
                    title: '内存峰值',
                    value: analysisData.memory.max.toFixed(0),
                    label: 'MB',
                    status: analysisData.memory.max < 500 ? 'good' : analysisData.memory.max < 800 ? 'warning' : 'bad'
                }});
            }}

            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = metrics.map(m => `
                <div class="metric-card ${{m.status}}">
                    <div class="metric-title">${{m.title}}</div>
                    <div class="metric-value">${{m.value}}</div>
                    <div class="metric-label">${{m.label}}</div>
                </div>
            `).join('');
        }}

        // 渲染问题列表
        function renderIssues() {{
            const issuesList = document.getElementById('issuesList');
            const issues = analysisData.issues || [];

            if (issues.length === 0) {{
                issuesList.innerHTML = '<p style="color: #27AE60; font-size: 1.2em;">✓ 未检测到性能问题</p>';
                return;
            }}

            issuesList.innerHTML = issues.map(issue => `
                <div class="issue-item ${{issue.severity}}">
                    <span class="issue-severity ${{issue.severity}}">${{issue.severity.toUpperCase()}}</span>
                    <strong>${{issue.category}}</strong>: ${{issue.description}}
                    <p style="margin-top: 10px; color: #7F8C8D;"><strong>建议:</strong> ${{issue.suggestion}}</p>
                </div>
            `).join('');
        }}

        // 渲染建议列表
        function renderRecommendations() {{
            const recList = document.getElementById('recommendationsList');
            const recommendations = analysisData.recommendations || [];

            if (recommendations.length === 0) {{
                recList.innerHTML = '<p style="color: #7F8C8D;">暂无优化建议</p>';
                return;
            }}

            recList.innerHTML = recommendations.map(rec => `
                <div class="recommendation-card">
                    <h3>${{rec.category}} [优先级: ${{rec.priority.toUpperCase()}}]</h3>
                    <ul>
                        ${{rec.suggestions.map(s => `<li>${{s}}</li>`).join('')}}
                    </ul>
                </div>
            `).join('');
        }}

        // 创建FPS时间线图表
        function createFPSTimeline() {{
            const ctx = document.getElementById('fpsTimelineChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: [
                        {{
                            label: 'FPS',
                            data: chartData.fps,
                            borderColor: '#3498DB',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4
                        }},
                        {{
                            label: '异常帧',
                            data: chartData.fps_anomaly || [],
                            type: 'scatter',
                            backgroundColor: '#E74C3C',
                            pointRadius: 8,
                            pointStyle: 'cross'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        annotation: {{
                            annotations: {{
                                line1: {{
                                    type: 'line',
                                    yMin: 60,
                                    yMax: 60,
                                    borderColor: '#27AE60',
                                    borderWidth: 2,
                                    borderDash: [10, 5],
                                    label: {{
                                        content: '60 FPS',
                                        enabled: true,
                                        position: 'end'
                                    }}
                                }},
                                line2: {{
                                    type: 'line',
                                    yMin: 30,
                                    yMax: 30,
                                    borderColor: '#F39C12',
                                    borderWidth: 2,
                                    borderDash: [10, 5],
                                    label: {{
                                        content: '30 FPS',
                                        enabled: true,
                                        position: 'end'
                                    }}
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'FPS'
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 创建FPS分布图
        function createFPSDistribution() {{
            const ctx = document.getElementById('fpsDistributionChart');
            if (!ctx) return;

            const fps = analysisData.chart_data.fps;
            const binCount = 30;
            const min = Math.min(...fps);
            const max = Math.max(...fps);
            const binSize = (max - min) / binCount;

            const bins = new Array(binCount).fill(0);
            fps.forEach(value => {{
                const binIndex = Math.min(Math.floor((value - min) / binSize), binCount - 1);
                bins[binIndex]++;
            }});

            const labels = Array.from({{length: binCount}}, (_, i) => 
                (min + i * binSize).toFixed(0) + '-' + (min + (i + 1) * binSize).toFixed(0)
            );

            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: '频次',
                        data: bins,
                        backgroundColor: '#9B59B6',
                        borderColor: '#8E44AD',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'FPS区间'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '频次'
                            }},
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        }}

        // 创建内存图表
        function createMemoryChart() {{
            const ctx = document.getElementById('memoryChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;
            const datasets = [];

            if (chartData.memory_total) {{
                datasets.push({{
                    label: '总内存',
                    data: chartData.memory_total,
                    borderColor: '#E74C3C',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4
                }});
            }}

            if (chartData.memory_mono) {{
                datasets.push({{
                    label: 'Mono内存',
                    data: chartData.memory_mono,
                    borderColor: '#3498DB',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }});
            }}

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '内存 (MB)'
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 创建GC图表
        function createGCChart() {{
            const ctx = document.getElementById('gcChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;

            if (!chartData.gc_alloc) {{
                ctx.parentElement.innerHTML = '<p style="color: #7F8C8D;">无GC数据</p>';
                return;
            }}

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: [{{
                        label: 'GC分配',
                        data: chartData.gc_alloc,
                        borderColor: '#F39C12',
                        backgroundColor: 'rgba(243, 156, 18, 0.2)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'GC分配 (KB)'
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 创建CPU/GPU图表
        function createCPUGPUChart() {{
            const ctx = document.getElementById('cpuGpuChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;
            const datasets = [];

            if (chartData.cpu_time) {{
                datasets.push({{
                    label: 'CPU时间',
                    data: chartData.cpu_time,
                    borderColor: '#E74C3C',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }});
            }}

            if (chartData.gpu_time) {{
                datasets.push({{
                    label: 'GPU时间',
                    data: chartData.gpu_time,
                    borderColor: '#9B59B6',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4
                }});
            }}

            if (datasets.length === 0) {{
                ctx.parentElement.innerHTML = '<p style="color: #7F8C8D;">无CPU/GPU数据</p>';
                return;
            }}

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: '时间 (ms)'
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 创建DrawCalls图表
        function createDrawCallsChart() {{
            const ctx = document.getElementById('drawCallsChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;

            if (!chartData.draw_calls) {{
                ctx.parentElement.innerHTML = '<p style="color: #7F8C8D;">无渲染数据</p>';
                return;
            }}

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: [{{
                        label: 'Draw Calls',
                        data: chartData.draw_calls,
                        borderColor: '#16A085',
                        backgroundColor: 'rgba(22, 160, 133, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Draw Calls'
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 创建概览图表
        function createOverviewChart() {{
            const ctx = document.getElementById('overviewChart');
            if (!ctx) return;

            const chartData = analysisData.chart_data;

            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: chartData.timestamps,
                    datasets: [
                        {{
                            label: 'FPS',
                            data: chartData.fps,
                            borderColor: '#3498DB',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            yAxisID: 'y',
                            borderWidth: 2.5,
                            fill: true,
                            tension: 0.4
                        }},
                        {{
                            label: '总内存 (MB)',
                            data: chartData.memory_total || [],
                            borderColor: '#E74C3C',
                            yAxisID: 'y1',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: '时间 (秒)'
                            }}
                        }},
                        y: {{
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {{
                                display: true,
                                text: 'FPS'
                            }}
                        }},
                        y1: {{
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {{
                                display: true,
                                text: '内存 (MB)'
                            }},
                            grid: {{
                                drawOnChartArea: false
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // 初始化
        document.addEventListener('DOMContentLoaded', function() {{
            renderMetrics();
            renderIssues();
            renderRecommendations();

            createOverviewChart();
            createFPSTimeline();
            createFPSDistribution();
            createMemoryChart();
            createGCChart();
            createCPUGPUChart();
            createDrawCallsChart();
        }});
    </script>
</body>
</html>'''


def main():
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python unity_performance_analyzer_interactive.py <csv_file> [platform]")
        print("示例: python unity_performance_analyzer_interactive.py report.csv Android")
        return

    csv_file = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else 'PC'

    analyzer = InteractivePerformanceAnalyzer(csv_file, platform)
    analyzer.load_data()
    analyzer.analyze()
    analyzer.generate_interactive_html()

    print("\n✓ 分析完成！交互式报告已在浏览器中打开")


if __name__ == '__main__':
    main()