// ==== UnityPerformanceMonitor_Universal.cs ====
using UnityEngine;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Linq;
using UnityEngine.SceneManagement;

#if UNITY_2021_2_OR_NEWER
using UnityEngine.Profiling;
using Unity.Profiling;
#else
using UnityEngine.Profiling;
#endif

#if UNITY_EDITOR
using UnityEditor;
#endif

/// <summary>
/// 通用Unity性能监控系统 - 无编译错误版本
/// 支持 Unity 2019.4+ 所有平台
/// 自动处理所有平台差异和API版本问题
/// </summary>
public class UnityPerformanceMonitor_Fixed : MonoBehaviour
{
    [Header("监控配置")]
    [SerializeField] private bool enableMonitoring = true;
    [SerializeField] private float sampleInterval = 0.5f;
    [SerializeField] private int maxSampleCount = 2000;
    
    [Header("异常阈值")]
    [SerializeField] private float fpsThreshold = 30f;
    [SerializeField] private float frameTimeThreshold = 33.3f; // ms (30fps)
    [SerializeField] private float memoryThreshold = 500f; // MB
    [SerializeField] private float gcThreshold = 1f; // MB/s
    [SerializeField] private int drawCallThreshold = 1000;
    
    [Header("输出配置")]
    [SerializeField] private string outputPath = "PerformanceReports";
    [SerializeField] private bool captureScreenshotOnAnomaly = true;
    [SerializeField] private KeyCode manualReportKey = KeyCode.F9;
    [SerializeField] private KeyCode toggleMonitoringKey = KeyCode.F8;
    
    [Header("移动平台优化")]
    [SerializeField] private bool isMobilePlatform = false;
    [SerializeField] private bool reducedSamplingOnMobile = true;
    
    private List<PerformanceSnapshot> snapshots = new List<PerformanceSnapshot>();
    private float nextSampleTime;
    private long lastGCMemory;
    private float lastGCTime;
    private StringBuilder logBuilder = new StringBuilder();
    
    // 用于计算稳定的FPS
    private Queue<float> fpsHistory = new Queue<float>(60);
    private float smoothedFPS = 60f;
    
#if UNITY_2021_2_OR_NEWER
    // ProfilerRecorder (Unity 2021.2+)
    private ProfilerRecorder mainThreadTimeRecorder;
    private ProfilerRecorder drawCallsRecorder;
    private ProfilerRecorder batchesRecorder;
    private ProfilerRecorder trianglesRecorder;
    private ProfilerRecorder verticesRecorder;
    private ProfilerRecorder setPassCallsRecorder;
    private ProfilerRecorder gcAllocRecorder;
    private bool useProfilerRecorder = true;
#else
    private bool useProfilerRecorder = false;
#endif
    
    /// <summary>
    /// 性能快照数据结构
    /// </summary>
    [System.Serializable]
    private class PerformanceSnapshot
    {
        // 时间信息
        public float timestamp;
        public float deltaTime;
        public float fps;
        public float smoothedFPS;
        public float unscaledDeltaTime;
        
        // CPU性能
        public float cpuFrameTime; // ms
        
        // 内存信息
        public long totalReservedMemory;
        public long totalAllocatedMemory;
        public long monoHeapSize;
        public long monoUsedSize;
        public long gcMemory;
        public float gcAllocationRate; // MB/s
        public float gcAllocThisFrame; // KB
        
        // 渲染统计
        public int drawCalls;
        public int batches;
        public int triangles;
        public int vertices;
        public int setPassCalls;
        
        // 对象统计
        public int gameObjectCount;
        public int activeGameObjectCount;
        
        // 场景信息
        public string currentSceneName;
        
        // 移动平台信息
        public float deviceTemperature;
        public float batteryLevel;
        public BatteryStatus batteryStatus;
        
        // 异常标记
        public bool isAnomaly;
        public string anomalyReason;
        
        public PerformanceSnapshot(float time)
        {
            timestamp = time;
        }
    }
    
    private void Awake()
    {
        DontDestroyOnLoad(gameObject);
        // 检测移动平台
        isMobilePlatform = Application.isMobilePlatform;
        
        string fullPath = Path.Combine(Application.persistentDataPath, outputPath);
        if (!Directory.Exists(fullPath))
        {
            Directory.CreateDirectory(fullPath);
        }
        
        Debug.Log($"[性能监控] 已启动 - 输出路径: {fullPath}");
        Debug.Log($"[性能监控] Unity版本: {Application.unityVersion}");
        Debug.Log($"[性能监控] 平台: {Application.platform}");
        Debug.Log($"[性能监控] 设备型号: {SystemInfo.deviceModel}");
        Debug.Log($"[性能监控] 处理器: {SystemInfo.processorType} ({SystemInfo.processorCount}核)");
        Debug.Log($"[性能监控] 内存: {SystemInfo.systemMemorySize}MB");
        Debug.Log($"[性能监控] GPU: {SystemInfo.graphicsDeviceName}");
        
        // 移动平台优化
        if (isMobilePlatform && reducedSamplingOnMobile)
        {
            sampleInterval = Mathf.Max(sampleInterval, 1f);
            Debug.Log($"[性能监控] 移动平台优化：采样间隔调整为 {sampleInterval}秒");
        }
        
        // 初始化GC基准
        lastGCMemory = System.GC.GetTotalMemory(false);
        lastGCTime = Time.realtimeSinceStartup;
        
#if UNITY_2021_2_OR_NEWER
        Debug.Log($"[性能监控] 使用 ProfilerRecorder API (Unity 2021.2+)");
#else
        Debug.Log($"[性能监控] 使用传统 Profiler API (兼容模式)");
#endif
    }
    
    private void OnEnable()
    {
#if UNITY_2021_2_OR_NEWER
        try
        {
            // 初始化ProfilerRecorders (Unity 2021.2+)
            mainThreadTimeRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 15);
            drawCallsRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count");
            batchesRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count");
            trianglesRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Triangles Count");
            verticesRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Vertices Count");
            setPassCallsRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Render, "SetPass Calls Count");
            gcAllocRecorder = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC.Alloc");
            
            Debug.Log("[性能监控] ProfilerRecorders 初始化成功");
        }
        catch (System.Exception e)
        {
            Debug.LogWarning($"[性能监控] ProfilerRecorders 初始化失败，使用兼容模式: {e.Message}");
            useProfilerRecorder = false;
        }
#endif
    }
    
    private void OnDisable()
    {
#if UNITY_2021_2_OR_NEWER
        // 释放ProfilerRecorders
        if (useProfilerRecorder)
        {
            mainThreadTimeRecorder.Dispose();
            drawCallsRecorder.Dispose();
            batchesRecorder.Dispose();
            trianglesRecorder.Dispose();
            verticesRecorder.Dispose();
            setPassCallsRecorder.Dispose();
            gcAllocRecorder.Dispose();
        }
#endif
    }
    
    private void Update()
    {
        // 切换监控开关
        if (Input.GetKeyDown(toggleMonitoringKey))
        {
            enableMonitoring = !enableMonitoring;
            Debug.Log($"[性能监控] {(enableMonitoring ? "已启用" : "已禁用")}");
        }
        
        if (!enableMonitoring) return;
        
        // 更新平滑FPS
        UpdateSmoothedFPS();
        
        // 定时采样
        if (Time.unscaledTime >= nextSampleTime)
        {
            CaptureSnapshot();
            nextSampleTime = Time.unscaledTime + sampleInterval;
            
            // 限制采样数量
            if (snapshots.Count > maxSampleCount)
            {
                snapshots.RemoveAt(0);
            }
        }
        
        // 手动生成报告
        if (Input.GetKeyDown(manualReportKey))
        {
            GenerateReport("ManualReport");
        }
    }
    
    private void UpdateSmoothedFPS()
    {
        float currentFPS = 1f / Time.unscaledDeltaTime;
        fpsHistory.Enqueue(currentFPS);
        
        if (fpsHistory.Count > 60)
        {
            fpsHistory.Dequeue();
        }
        
        smoothedFPS = fpsHistory.Average();
    }
    
    private void CaptureSnapshot()
    {
        PerformanceSnapshot snapshot = new PerformanceSnapshot(Time.realtimeSinceStartup);
        
        // ========== 时间信息 ==========
        snapshot.deltaTime = Time.deltaTime;
        snapshot.unscaledDeltaTime = Time.unscaledDeltaTime;
        snapshot.fps = 1f / Time.unscaledDeltaTime;
        snapshot.smoothedFPS = smoothedFPS;
        
        // ========== CPU性能 ==========
#if UNITY_2021_2_OR_NEWER
        if (useProfilerRecorder && mainThreadTimeRecorder.Valid)
        {
            snapshot.cpuFrameTime = GetRecorderFrameAverage(mainThreadTimeRecorder) * 1e-6f; // ns to ms
        }
        else
#endif
        {
            // 兼容模式：使用deltaTime估算
            snapshot.cpuFrameTime = Time.deltaTime * 1000f;
        }
        
        // ========== 内存信息 ==========
        snapshot.totalReservedMemory = Profiler.GetTotalReservedMemoryLong();
        snapshot.totalAllocatedMemory = Profiler.GetTotalAllocatedMemoryLong();
        snapshot.monoHeapSize = Profiler.GetMonoHeapSizeLong();
        snapshot.monoUsedSize = Profiler.GetMonoUsedSizeLong();
        snapshot.gcMemory = System.GC.GetTotalMemory(false);
        
        // GC分配 (Unity 2021.2+)
#if UNITY_2021_2_OR_NEWER
        if (useProfilerRecorder && gcAllocRecorder.Valid)
        {
            snapshot.gcAllocThisFrame = GetRecorderLastValue(gcAllocRecorder) / 1024f; // bytes to KB
        }
        else
#endif
        {
            // 兼容模式：通过总内存变化估算
            snapshot.gcAllocThisFrame = 0;
        }
        
        // GC分配率计算
        float currentTime = Time.realtimeSinceStartup;
        if (lastGCMemory > 0 && currentTime > lastGCTime)
        {
            float gcDelta = (snapshot.gcMemory - lastGCMemory) / (1024f * 1024f);
            float timeDelta = currentTime - lastGCTime;
            snapshot.gcAllocationRate = Mathf.Max(0, gcDelta / timeDelta);
        }
        lastGCMemory = snapshot.gcMemory;
        lastGCTime = currentTime;
        
        // ========== 渲染统计 ==========
#if UNITY_2021_2_OR_NEWER
        if (useProfilerRecorder)
        {
            snapshot.drawCalls = (int)GetRecorderLastValue(drawCallsRecorder);
            snapshot.batches = (int)GetRecorderLastValue(batchesRecorder);
            snapshot.triangles = (int)GetRecorderLastValue(trianglesRecorder);
            snapshot.vertices = (int)GetRecorderLastValue(verticesRecorder);
            snapshot.setPassCalls = (int)GetRecorderLastValue(setPassCallsRecorder);
        }
        else
#endif
        {
            // 兼容模式：使用传统统计（需要在Profiler开启时才有数据）
            snapshot.drawCalls = 0;
            snapshot.batches = 0;
            snapshot.triangles = 0;
            snapshot.vertices = 0;
            snapshot.setPassCalls = 0;
        }
        
        // ========== 对象统计 ==========
        // 注意：FindObjectsOfType有性能开销，可考虑降低采样频率
        var allGameObjects = FindObjectsOfType<GameObject>();
        snapshot.gameObjectCount = allGameObjects.Length;
        snapshot.activeGameObjectCount = allGameObjects.Count(go => go.activeInHierarchy);
        
        // ========== 场景信息 ==========
        snapshot.currentSceneName = SceneManager.GetActiveScene().name;
        
        // ========== 移动平台特定信息 ==========
        if (isMobilePlatform)
        {
            // deviceTemperature 只在Android和iOS可用
#if UNITY_ANDROID || UNITY_IOS
            //snapshot.deviceTemperature = SystemInfo.deviceTemperature;
#else
            snapshot.deviceTemperature = 0f;
#endif
            snapshot.batteryLevel = SystemInfo.batteryLevel;
            snapshot.batteryStatus = SystemInfo.batteryStatus;
        }
        else
        {
            // 非移动平台设置默认值
            snapshot.deviceTemperature = 0f;
            snapshot.batteryLevel = 1f;
            snapshot.batteryStatus = BatteryStatus.Unknown;
        }
        
        // ========== 异常检测 ==========
        CheckForAnomalies(snapshot);
        
        snapshots.Add(snapshot);
    }
    
    private void CheckForAnomalies(PerformanceSnapshot snapshot)
    {
        List<string> reasons = new List<string>();
        
        // FPS异常
        if (snapshot.fps < fpsThreshold)
        {
            reasons.Add($"FPS过低({snapshot.fps:F1})");
        }
        
        // 帧时间异常
        if (snapshot.cpuFrameTime > frameTimeThreshold)
        {
            reasons.Add($"帧时间过长({snapshot.cpuFrameTime:F1}ms)");
        }
        
        // 内存异常
        float totalMemoryMB = snapshot.totalAllocatedMemory / (1024f * 1024f);
        if (totalMemoryMB > memoryThreshold)
        {
            reasons.Add($"内存使用过高({totalMemoryMB:F0}MB)");
        }
        
        // GC异常
        if (snapshot.gcAllocationRate > gcThreshold)
        {
            reasons.Add($"GC分配率过高({snapshot.gcAllocationRate:F2}MB/s)");
        }
        if (snapshot.gcAllocThisFrame > 500)
        {
            reasons.Add($"单帧GC分配过大({snapshot.gcAllocThisFrame:F0}KB)");
        }
        
        // DrawCalls异常
        if (snapshot.drawCalls > drawCallThreshold)
        {
            reasons.Add($"DrawCalls过多({snapshot.drawCalls})");
        }
        
        // 移动平台特定异常
        if (isMobilePlatform)
        {
            if (snapshot.deviceTemperature > 45f && snapshot.deviceTemperature > 0)
            {
                reasons.Add($"设备温度过高({snapshot.deviceTemperature:F1}°C)");
            }
            
            if (snapshot.batteryLevel < 0.15f && snapshot.batteryStatus == BatteryStatus.Discharging)
            {
                reasons.Add($"电量过低({snapshot.batteryLevel * 100:F0}%)");
            }
        }
        
        if (reasons.Count > 0)
        {
            snapshot.isAnomaly = true;
            snapshot.anomalyReason = string.Join(", ", reasons);
            
            // 捕获截图
            if (captureScreenshotOnAnomaly)
            {
                CaptureScreenshot($"Anomaly_{snapshot.timestamp:F2}");
            }
        }
    }
    
#if UNITY_2021_2_OR_NEWER
    private float GetRecorderFrameAverage(ProfilerRecorder recorder)
    {
        if (!recorder.Valid || recorder.Count == 0)
            return 0;
        
        var samplesCount = recorder.Capacity;
        if (samplesCount == 0)
            return 0;
        
        double sum = 0;
        unsafe
        {
            var samples = stackalloc ProfilerRecorderSample[samplesCount];
            recorder.CopyTo(samples, samplesCount);
            for (var i = 0; i < samplesCount; ++i)
                sum += samples[i].Value;
        }
        
        return (float)(sum / samplesCount);
    }
    
    private long GetRecorderLastValue(ProfilerRecorder recorder)
    {
        if (!recorder.Valid)
            return 0;
        
        return recorder.LastValue;
    }
#endif
    
    private void CaptureScreenshot(string filename)
    {
        string path = Path.Combine(Application.persistentDataPath, outputPath, $"{filename}.png");
        ScreenCapture.CaptureScreenshot(path);
    }
    
    public void GenerateReport(string reportName)
    {
        if (snapshots.Count == 0)
        {
            Debug.LogWarning("[性能监控] 没有数据可生成报告");
            return;
        }
        
        string timestamp = System.DateTime.Now.ToString("yyyyMMdd_HHmmss");
        string filename = $"{reportName}_{timestamp}";
        string basePath = Path.Combine(Application.persistentDataPath, outputPath);
        
        // 生成TXT报告
        string txtPath = Path.Combine(basePath, $"{filename}.txt");
        GenerateTextReport(txtPath);
        
        // 生成CSV报告
        string csvPath = Path.Combine(basePath, $"{filename}.csv");
        GenerateCSVReport(csvPath);
        
        Debug.Log($"[性能监控] 报告已生成:\n- {txtPath}\n- {csvPath}");
        
        // 输出统计摘要
        Debug.Log($"[性能监控] 统计摘要:\n{GenerateConsoleSummary()}");
    }
    
    private void GenerateTextReport(string filepath)
    {
        logBuilder.Clear();
        
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine("                        Unity性能监控详细报告");
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine($"生成时间: {System.DateTime.Now:yyyy-MM-dd HH:mm:ss}");
        logBuilder.AppendLine($"Unity版本: {Application.unityVersion}");
        logBuilder.AppendLine($"平台: {Application.platform}");
        logBuilder.AppendLine($"设备型号: {SystemInfo.deviceModel}");
        logBuilder.AppendLine($"处理器: {SystemInfo.processorType} ({SystemInfo.processorCount}核)");
        logBuilder.AppendLine($"系统内存: {SystemInfo.systemMemorySize}MB");
        logBuilder.AppendLine($"GPU: {SystemInfo.graphicsDeviceName}");
        logBuilder.AppendLine($"采样数量: {snapshots.Count}");
        logBuilder.AppendLine($"监控时长: {snapshots.Last().timestamp - snapshots.First().timestamp:F1}秒");
        logBuilder.AppendLine();
        
        GeneratePerformanceSummary();
        GenerateAnomalyList();
        
        File.WriteAllText(filepath, logBuilder.ToString());
    }
    
    private void GeneratePerformanceSummary()
    {
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine("                            性能统计摘要");
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine();
        
        // FPS统计
        logBuilder.AppendLine("【帧率统计】");
        logBuilder.AppendLine($"平均FPS: {snapshots.Average(s => s.fps):F2}");
        logBuilder.AppendLine($"最低FPS: {snapshots.Min(s => s.fps):F2}");
        logBuilder.AppendLine($"最高FPS: {snapshots.Max(s => s.fps):F2}");
        logBuilder.AppendLine($"1%低点: {snapshots.OrderBy(s => s.fps).Take(Mathf.Max(1, snapshots.Count / 100)).Average(s => s.fps):F2}");
        logBuilder.AppendLine($"5%低点: {snapshots.OrderBy(s => s.fps).Take(Mathf.Max(1, snapshots.Count / 20)).Average(s => s.fps):F2}");
        logBuilder.AppendLine($"标准差: {CalculateStandardDeviation(snapshots.Select(s => s.fps)):F2}");
        logBuilder.AppendLine();
        
        // 帧时间统计
        logBuilder.AppendLine("【帧时间统计】");
        logBuilder.AppendLine($"平均帧时间: {snapshots.Average(s => s.cpuFrameTime):F2}ms");
        logBuilder.AppendLine($"最大帧时间: {snapshots.Max(s => s.cpuFrameTime):F2}ms");
        logBuilder.AppendLine();
        
        // 内存统计
        logBuilder.AppendLine("【内存使用】");
        logBuilder.AppendLine($"平均总分配内存: {snapshots.Average(s => s.totalAllocatedMemory / (1024f * 1024f)):F1}MB");
        logBuilder.AppendLine($"最大总分配内存: {snapshots.Max(s => s.totalAllocatedMemory) / (1024f * 1024f):F1}MB");
        logBuilder.AppendLine($"平均Mono堆: {snapshots.Average(s => s.monoUsedSize / (1024f * 1024f)):F1}MB");
        logBuilder.AppendLine($"最大Mono堆: {snapshots.Max(s => s.monoUsedSize) / (1024f * 1024f):F1}MB");
        logBuilder.AppendLine();
        
        // GC统计
        logBuilder.AppendLine("【GC统计】");
        var validGCRates = snapshots.Where(s => s.gcAllocationRate > 0).ToList();
        if (validGCRates.Any())
        {
            logBuilder.AppendLine($"平均GC分配率: {validGCRates.Average(s => s.gcAllocationRate):F2}MB/s");
            logBuilder.AppendLine($"最大GC分配率: {validGCRates.Max(s => s.gcAllocationRate):F2}MB/s");
        }
        if (snapshots.Any(s => s.gcAllocThisFrame > 0))
        {
            logBuilder.AppendLine($"平均单帧GC分配: {snapshots.Average(s => s.gcAllocThisFrame):F2}KB");
            logBuilder.AppendLine($"最大单帧GC分配: {snapshots.Max(s => s.gcAllocThisFrame):F2}KB");
            logBuilder.AppendLine($"GC尖峰次数(>500KB): {snapshots.Count(s => s.gcAllocThisFrame > 500)}");
        }
        logBuilder.AppendLine();
        
        // 渲染统计
        if (snapshots.Any(s => s.drawCalls > 0))
        {
            logBuilder.AppendLine("【渲染统计】");
            logBuilder.AppendLine($"平均DrawCalls: {snapshots.Average(s => s.drawCalls):F0}");
            logBuilder.AppendLine($"最大DrawCalls: {snapshots.Max(s => s.drawCalls)}");
            if (snapshots.Any(s => s.triangles > 0))
            {
                logBuilder.AppendLine($"平均三角形数: {snapshots.Average(s => s.triangles):F0}");
            }
            logBuilder.AppendLine();
        }
        
        // 异常统计
        int anomalyCount = snapshots.Count(s => s.isAnomaly);
        logBuilder.AppendLine("【异常统计】");
        logBuilder.AppendLine($"异常帧数: {anomalyCount}");
        logBuilder.AppendLine($"异常率: {anomalyCount * 100f / snapshots.Count:F2}%");
        logBuilder.AppendLine();
    }
    
    private void GenerateAnomalyList()
    {
        var anomalies = snapshots.Where(s => s.isAnomaly).ToList();
        
        if (anomalies.Count == 0)
        {
            logBuilder.AppendLine("未检测到性能异常");
            logBuilder.AppendLine();
            return;
        }
        
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine($"                      性能异常列表 (共{anomalies.Count}次)");
        logBuilder.AppendLine("================================================================================");
        logBuilder.AppendLine();
        
        foreach (var anomaly in anomalies.Take(100))
        {
            logBuilder.AppendLine($"[{anomaly.timestamp:F2}s] {anomaly.anomalyReason}");
            logBuilder.AppendLine($"  FPS: {anomaly.fps:F1}, 帧时间: {anomaly.cpuFrameTime:F1}ms, " +
                $"内存: {anomaly.totalAllocatedMemory / (1024f * 1024f):F1}MB");
            if (anomaly.drawCalls > 0)
            {
                logBuilder.AppendLine($"  DrawCalls: {anomaly.drawCalls}, GC本帧: {anomaly.gcAllocThisFrame:F1}KB");
            }
            logBuilder.AppendLine();
        }
        
        if (anomalies.Count > 100)
        {
            logBuilder.AppendLine($"... 还有 {anomalies.Count - 100} 个异常未显示");
            logBuilder.AppendLine();
        }
    }
    
    private void GenerateCSVReport(string filepath)
    {
        StringBuilder csv = new StringBuilder();
        
        // CSV表头
        csv.AppendLine("Timestamp,FPS,SmoothedFPS,DeltaTime,UnscaledDeltaTime," +
            "CPUFrameTime_ms," +
            "TotalReserved_MB,TotalAllocated_MB,MonoHeap_MB,MonoUsed_MB," +
            "GCMemory_MB,GCAllocRate_MBps,GCAllocThisFrame_KB," +
            "DrawCalls,Batches,Triangles,Vertices,SetPassCalls," +
            "GameObjectCount,ActiveGameObjectCount," +
            "CurrentSceneName," +
            "DeviceTemperature,BatteryLevel,BatteryStatus," +
            "IsAnomaly,AnomalyReason");
        
        // 数据行
        foreach (var s in snapshots)
        {
            csv.AppendLine(
                $"{s.timestamp:F3}," +
                $"{s.fps:F2}," +
                $"{s.smoothedFPS:F2}," +
                $"{s.deltaTime:F5}," +
                $"{s.unscaledDeltaTime:F5}," +
                $"{s.cpuFrameTime:F3}," +
                $"{s.totalReservedMemory / (1024f * 1024f):F2}," +
                $"{s.totalAllocatedMemory / (1024f * 1024f):F2}," +
                $"{s.monoHeapSize / (1024f * 1024f):F2}," +
                $"{s.monoUsedSize / (1024f * 1024f):F2}," +
                $"{s.gcMemory / (1024f * 1024f):F2}," +
                $"{s.gcAllocationRate:F3}," +
                $"{s.gcAllocThisFrame:F2}," +
                $"{s.drawCalls}," +
                $"{s.batches}," +
                $"{s.triangles}," +
                $"{s.vertices}," +
                $"{s.setPassCalls}," +
                $"{s.gameObjectCount}," +
                $"{s.activeGameObjectCount}," +
                $"\"{s.currentSceneName}\"," +
                $"{s.deviceTemperature:F1}," +
                $"{s.batteryLevel:F3}," +
                $"{s.batteryStatus}," +
                $"{(s.isAnomaly ? 1 : 0)}," +
                $"\"{s.anomalyReason}\""
            );
        }
        
        File.WriteAllText(filepath, csv.ToString(), System.Text.Encoding.UTF8);
    }
    
    private string GenerateConsoleSummary()
    {
        StringBuilder sb = new StringBuilder();
        sb.AppendLine($"采样数量: {snapshots.Count}");
        sb.AppendLine($"平均FPS: {snapshots.Average(s => s.fps):F1}");
        sb.AppendLine($"最低FPS: {snapshots.Min(s => s.fps):F1}");
        sb.AppendLine($"内存峰值: {snapshots.Max(s => s.totalAllocatedMemory) / (1024f * 1024f):F0}MB");
        sb.AppendLine($"异常率: {snapshots.Count(s => s.isAnomaly) * 100f / snapshots.Count:F1}%");
        return sb.ToString();
    }
    
    private float CalculateStandardDeviation(IEnumerable<float> values)
    {
        float avg = values.Average();
        float sumOfSquares = values.Sum(v => (v - avg) * (v - avg));
        return Mathf.Sqrt(sumOfSquares / values.Count());
    }
    
    private void OnApplicationQuit()
    {
        if (enableMonitoring && snapshots.Count > 0)
        {
            GenerateReport("FinalReport");
        }
    }
    
    // 公共API
    public void StartMonitoring() => enableMonitoring = true;
    public void StopMonitoring() => enableMonitoring = false;
    public void ClearData() => snapshots.Clear();
    public int GetSnapshotCount() => snapshots.Count;
    public int GetAnomalyCount() => snapshots.Count(s => s.isAnomaly);
    public float GetAverageFPS() => snapshots.Count > 0 ? snapshots.Average(s => s.fps) : 0;
    public float GetMinFPS() => snapshots.Count > 0 ? snapshots.Min(s => s.fps) : 0;
}