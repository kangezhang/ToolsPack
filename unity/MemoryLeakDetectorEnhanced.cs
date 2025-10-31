// ==== MemoryLeakDetectorEnhanced.cs ====
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.SceneManagement;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;

/// <summary>
/// Unity内存泄漏增强检测系统
/// 核心功能：
/// 1. 对象级追踪 - 定位具体泄漏的Texture、GameObject
/// 2. 资源来源分析 - 识别Resources、Addressables等加载方式
/// 3. 智能问题分析 - 自动判断是程序问题还是美术问题
/// 4. 责任划分 - 明确程序组、美术组、TA的责任和占比
/// 5. 优化建议 - 提供具体可执行的解决方案
/// 6. 预估修复时间 - 评估各问题的修复周期
/// </summary>
public class MemoryLeakDetectorEnhanced : MonoBehaviour
{
    [Header("监控配置")]
    [Tooltip("内存增长阈值(MB)")]
    public float memoryGrowthThreshold = 50f;
    
    [Tooltip("监控采样间隔(秒)")]
    public float sampleInterval = 1f;
    
    [Tooltip("对象快照间隔(秒)")]
    public float snapshotInterval = 5f;
    
    [Tooltip("是否启用深度对象追踪")]
    public bool enableDeepTracking = true;
    
    [Tooltip("是否自动生成报告")]
    public bool autoGenerateReport = true;
    
    [Tooltip("泄漏警报阈值(MB/分钟)")]
    public float leakRateThreshold = 10f;

    [Header("追踪选项")]
    public bool trackTextures = true;
    public bool trackGameObjects = true;
    public bool trackMeshes = true;
    public bool trackAudioClips = true;
    public bool trackMaterials = true;

    // 内部数据
    private List<MemorySample> samples = new List<MemorySample>();
    private MemorySample baselineSample;
    private Dictionary<string, SceneMemoryProfile> sceneProfiles = new Dictionary<string, SceneMemoryProfile>();
    private List<MemoryLeakEvent> detectedLeaks = new List<MemoryLeakEvent>();
    
    // 对象追踪
    private Dictionary<int, ObjectSnapshot> previousSnapshot = new Dictionary<int, ObjectSnapshot>();
    private Dictionary<int, ObjectSnapshot> currentSnapshot = new Dictionary<int, ObjectSnapshot>();
    private List<LeakedObjectInfo> leakedObjects = new List<LeakedObjectInfo>();
    
    private float nextSampleTime;
    private float nextSnapshotTime;
    private bool isMonitoring = true;
    
    // UI相关
    private Rect windowRect = new Rect(10, 10, 500, 700);
    private Vector2 scrollPosition;
    private bool showWindow = true;
    private int selectedTab = 0;
    
    // 统计数据
    private long peakMemory = 0;
    private float totalRunTime = 0;
    
    #region 数据结构
    
    [System.Serializable]
    public class MemorySample
    {
        public float timestamp;
        public long totalAllocated;
        public long totalReserved;
        public long monoUsed;
        public long monoHeap;
        public long textureMemory;
        public long meshMemory;
        public long audioMemory;
        public long materialMemory;
        public int gameObjectCount;
        public int componentCount;
        public int textureCount;
        public int meshCount;
        public int audioClipCount;
        public int materialCount;
        public string sceneName;
        public float fps;
        
        public long GetTotalMB() => totalAllocated / (1024 * 1024);
    }
    
    [System.Serializable]
    public class SceneMemoryProfile
    {
        public string sceneName;
        public long entryMemory;
        public long exitMemory;
        public long peakMemory;
        public float duration;
        public List<string> warnings = new List<string>();
    }
    
    [System.Serializable]
    public class MemoryLeakEvent
    {
        public float timestamp;
        public string leakType;
        public long memoryBefore;
        public long memoryAfter;
        public long leakSize;
        public string sceneName;
        public string description;
        public LeakSeverity severity;
        public List<string> suspectedObjects = new List<string>();
        
        public enum LeakSeverity
        {
            Low,
            Medium,
            High,
            Critical
        }
    }
    
    [System.Serializable]
    public class ObjectSnapshot
    {
        public int instanceID;
        public string objectName;
        public string objectType;
        public long memorySize;
        public string sceneName;
        public float captureTime;
        public string loadSource;
        public bool isDontDestroyOnLoad;
    }
    
    [System.Serializable]
    public class LeakedObjectInfo
    {
        public ObjectSnapshot snapshot;
        public float leakDetectedTime;
        public int survivedSnapshots;
        public string leakReason;
    }
    
    // 问题分析结果
    [System.Serializable]
    public class ProblemAnalysis
    {
        public string category;
        public string responsibility;
        public string severity;
        public long memoryImpact;
        public List<string> specificIssues = new List<string>();
        public List<string> rootCauses = new List<string>();
        public List<string> solutions = new List<string>();
        public int estimatedDays;
    }
    
    #endregion
    
    #region Unity生命周期
    
    void Awake()
    {
        if (FindObjectsOfType<MemoryLeakDetectorEnhanced>().Length > 1)
        {
            Destroy(gameObject);
            return;
        }
        
        DontDestroyOnLoad(gameObject);
        
        baselineSample = CaptureSample();
        sceneProfiles[SceneManager.GetActiveScene().name] = new SceneMemoryProfile
        {
            sceneName = baselineSample.sceneName,
            entryMemory = baselineSample.totalAllocated
        };
        
        Debug.Log($"<color=cyan>【增强内存监控】已启动 - 基准内存: {baselineSample.GetTotalMB()}MB</color>");
        
        SceneManager.sceneLoaded += OnSceneLoaded;
        SceneManager.sceneUnloaded += OnSceneUnloaded;
        
        if (enableDeepTracking)
        {
            CaptureObjectSnapshot();
        }
    }
    
    void Update()
    {
        if (!isMonitoring) return;
        
        totalRunTime += Time.deltaTime;
        
        if (Time.time >= nextSampleTime)
        {
            nextSampleTime = Time.time + sampleInterval;
            
            MemorySample sample = CaptureSample();
            samples.Add(sample);
            
            DetectLeaks(sample);
            
            if (samples.Count > 1000)
            {
                samples.RemoveAt(0);
            }
        }
        
        if (enableDeepTracking && Time.time >= nextSnapshotTime)
        {
            nextSnapshotTime = Time.time + snapshotInterval;
            CaptureObjectSnapshot();
            AnalyzeLeakedObjects();
        }
        
        if (Input.GetKeyDown(KeyCode.F9))
        {
            showWindow = !showWindow;
        }
        
        if (Input.GetKeyDown(KeyCode.F10))
        {
            GenerateDetailedReport();
        }
        
        if (Input.GetKeyDown(KeyCode.F11))
        {
            ForceGarbageCollection();
        }
        
        if (Input.GetKeyDown(KeyCode.F12))
        {
            DumpLeakedObjects();
        }
    }
    
    void OnGUI()
    {
        if (!showWindow) return;
        
        windowRect = GUI.Window(0, windowRect, DrawMonitorWindow, "增强内存泄漏检测器");
    }
    
    void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
        SceneManager.sceneUnloaded -= OnSceneUnloaded;
        
        if (autoGenerateReport && samples.Count > 0)
        {
            GenerateDetailedReport();
        }
    }
    
    #endregion
    
    #region 内存采样
    
    private MemorySample CaptureSample()
    {
        var sample = new MemorySample
        {
            timestamp = Time.time,
            totalAllocated = Profiler.GetTotalAllocatedMemoryLong(),
            totalReserved = Profiler.GetTotalReservedMemoryLong(),
            monoUsed = Profiler.GetMonoUsedSizeLong(),
            monoHeap = Profiler.GetMonoHeapSizeLong(),
            sceneName = SceneManager.GetActiveScene().name,
            fps = 1f / Time.deltaTime,
            gameObjectCount = FindObjectsOfType<GameObject>().Length,
            componentCount = FindObjectsOfType<Component>().Length
        };
        
        if (trackTextures)
        {
            var textures = Resources.FindObjectsOfTypeAll<Texture>();
            sample.textureMemory = textures.Sum(t => t != null ? Profiler.GetRuntimeMemorySizeLong(t) : 0);
            sample.textureCount = textures.Length;
        }
        
        if (trackMeshes)
        {
            var meshes = Resources.FindObjectsOfTypeAll<Mesh>();
            sample.meshMemory = meshes.Sum(m => m != null ? Profiler.GetRuntimeMemorySizeLong(m) : 0);
            sample.meshCount = meshes.Length;
        }
        
        if (trackAudioClips)
        {
            var clips = Resources.FindObjectsOfTypeAll<AudioClip>();
            sample.audioMemory = clips.Sum(c => c != null ? Profiler.GetRuntimeMemorySizeLong(c) : 0);
            sample.audioClipCount = clips.Length;
        }
        
        if (trackMaterials)
        {
            var materials = Resources.FindObjectsOfTypeAll<Material>();
            sample.materialMemory = materials.Sum(m => m != null ? Profiler.GetRuntimeMemorySizeLong(m) : 0);
            sample.materialCount = materials.Length;
        }
        
        if (sample.totalAllocated > peakMemory)
        {
            peakMemory = sample.totalAllocated;
        }
        
        return sample;
    }
    
    #endregion
    
    #region 对象快照与追踪
    
    private void CaptureObjectSnapshot()
    {
        previousSnapshot = new Dictionary<int, ObjectSnapshot>(currentSnapshot);
        currentSnapshot.Clear();
        
        string currentScene = SceneManager.GetActiveScene().name;
        
        if (trackTextures)
        {
            var textures = Resources.FindObjectsOfTypeAll<Texture>();
            foreach (var tex in textures)
            {
                if (tex == null || IsEditorAsset(tex)) continue;
                
                var snapshot = new ObjectSnapshot
                {
                    instanceID = tex.GetInstanceID(),
                    objectName = tex.name,
                    objectType = tex.GetType().Name,
                    memorySize = Profiler.GetRuntimeMemorySizeLong(tex),
                    sceneName = currentScene,
                    captureTime = Time.time,
                    loadSource = DetectLoadSource(tex),
                    isDontDestroyOnLoad = IsDontDestroyOnLoad(tex)
                };
                
                currentSnapshot[snapshot.instanceID] = snapshot;
            }
        }
        
        if (trackGameObjects)
        {
            var gameObjects = FindObjectsOfType<GameObject>();
            foreach (var go in gameObjects)
            {
                if (go == null || go.hideFlags == HideFlags.HideAndDontSave) continue;
                
                var snapshot = new ObjectSnapshot
                {
                    instanceID = go.GetInstanceID(),
                    objectName = go.name,
                    objectType = "GameObject",
                    memorySize = CalculateGameObjectMemory(go),
                    sceneName = go.scene.name,
                    captureTime = Time.time,
                    loadSource = go.scene.name == currentScene ? "Scene" : "DontDestroyOnLoad",
                    isDontDestroyOnLoad = IsDontDestroyOnLoad(go)
                };
                
                currentSnapshot[snapshot.instanceID] = snapshot;
            }
        }
        
        if (trackMeshes)
        {
            var meshes = Resources.FindObjectsOfTypeAll<Mesh>();
            foreach (var mesh in meshes)
            {
                if (mesh == null || IsEditorAsset(mesh)) continue;
                
                var snapshot = new ObjectSnapshot
                {
                    instanceID = mesh.GetInstanceID(),
                    objectName = mesh.name,
                    objectType = "Mesh",
                    memorySize = Profiler.GetRuntimeMemorySizeLong(mesh),
                    sceneName = currentScene,
                    captureTime = Time.time,
                    loadSource = DetectLoadSource(mesh)
                };
                
                currentSnapshot[snapshot.instanceID] = snapshot;
            }
        }
        
        if (trackMaterials)
        {
            var materials = Resources.FindObjectsOfTypeAll<Material>();
            foreach (var mat in materials)
            {
                if (mat == null || IsEditorAsset(mat)) continue;
                
                var snapshot = new ObjectSnapshot
                {
                    instanceID = mat.GetInstanceID(),
                    objectName = mat.name,
                    objectType = "Material",
                    memorySize = Profiler.GetRuntimeMemorySizeLong(mat),
                    sceneName = currentScene,
                    captureTime = Time.time,
                    loadSource = DetectLoadSource(mat)
                };
                
                currentSnapshot[snapshot.instanceID] = snapshot;
            }
        }
    }
    
    private void AnalyzeLeakedObjects()
    {
        if (previousSnapshot.Count == 0) return;
        
        foreach (var kvp in previousSnapshot)
        {
            int instanceID = kvp.Key;
            ObjectSnapshot oldSnapshot = kvp.Value;
            
            if (currentSnapshot.ContainsKey(instanceID))
            {
                var existingLeak = leakedObjects.FirstOrDefault(l => l.snapshot.instanceID == instanceID);
                
                if (existingLeak != null)
                {
                    existingLeak.survivedSnapshots++;
                    
                    if (existingLeak.survivedSnapshots >= 3 && !IsInCurrentScene(oldSnapshot))
                    {
                        existingLeak.leakReason = "对象长时间存活且不属于当前场景";
                    }
                }
                else
                {
                    if (!IsInCurrentScene(oldSnapshot) && !oldSnapshot.isDontDestroyOnLoad)
                    {
                        var leak = new LeakedObjectInfo
                        {
                            snapshot = oldSnapshot,
                            leakDetectedTime = Time.time,
                            survivedSnapshots = 1,
                            leakReason = "对象不属于当前场景但未被销毁"
                        };
                        
                        leakedObjects.Add(leak);
                    }
                }
            }
        }
        
        leakedObjects.RemoveAll(l => !currentSnapshot.ContainsKey(l.snapshot.instanceID));
        leakedObjects = leakedObjects.OrderByDescending(l => l.snapshot.memorySize).ToList();
    }
    
    private bool IsInCurrentScene(ObjectSnapshot snapshot)
    {
        string currentScene = SceneManager.GetActiveScene().name;
        return snapshot.sceneName == currentScene;
    }
    
    private bool IsEditorAsset(Object obj)
    {
        if (obj.hideFlags == HideFlags.HideAndDontSave) return true;
        if (obj.hideFlags == HideFlags.NotEditable) return true;
        if (obj.name.Contains("Font Material")) return true;
        if (obj.name.Contains("Default-")) return true;
        return false;
    }
    
    private bool IsDontDestroyOnLoad(Object obj)
    {
        if (obj is GameObject go)
        {
            return go.scene.name == "DontDestroyOnLoad";
        }
        return false;
    }
    
    private string DetectLoadSource(Object obj)
    {
        string name = obj.name.ToLower();
        
        if (name.Contains("resources"))
        {
            return "Resources";
        }
        else if (name.Contains("addressable"))
        {
            return "Addressables";
        }
        else if (name.Contains("assetbundle") || name.Contains("bundle"))
        {
            return "AssetBundle";
        }
        else
        {
            return "Runtime";
        }
    }
    
    private long CalculateGameObjectMemory(GameObject go)
    {
        long total = 0;
        
        var components = go.GetComponents<Component>();
        foreach (var comp in components)
        {
            if (comp != null)
            {
                total += Profiler.GetRuntimeMemorySizeLong(comp);
            }
        }
        
        return total;
    }
    
    #endregion
    
    #region 泄漏检测
    
    private void DetectLeaks(MemorySample currentSample)
    {
        if (samples.Count < 10) return;
        
        DetectContinuousGrowth(currentSample);
        DetectSuddenLeak(currentSample);
        DetectTextureLeakEnhanced(currentSample);
        DetectGameObjectLeakEnhanced(currentSample);
    }
    
    private void DetectContinuousGrowth(MemorySample current)
    {
        var recentSamples = samples.Skip(Mathf.Max(0, samples.Count - 60)).ToList();
        if (recentSamples.Count < 60) return;
        
        float duration = recentSamples.Last().timestamp - recentSamples.First().timestamp;
        if (duration < 30f) return;
        
        long memoryGrowth = recentSamples.Last().totalAllocated - recentSamples.First().totalAllocated;
        float growthRateMBPerMin = (memoryGrowth / (1024f * 1024f)) / (duration / 60f);
        
        if (growthRateMBPerMin > leakRateThreshold)
        {
            var leak = new MemoryLeakEvent
            {
                timestamp = Time.time,
                leakType = "持续内存增长",
                memoryBefore = recentSamples.First().totalAllocated,
                memoryAfter = current.totalAllocated,
                leakSize = memoryGrowth,
                sceneName = current.sceneName,
                description = $"检测到持续内存增长: {growthRateMBPerMin:F2}MB/分钟",
                severity = GetSeverity(memoryGrowth)
            };
            
            AddSuspectedObjectsToLeak(leak);
            detectedLeaks.Add(leak);
        }
    }
    
    private void DetectSuddenLeak(MemorySample current)
    {
        if (samples.Count < 2) return;
        
        var previous = samples[samples.Count - 2];
        long growth = current.totalAllocated - previous.totalAllocated;
        float growthMB = growth / (1024f * 1024f);
        
        if (growthMB > memoryGrowthThreshold)
        {
            var leak = new MemoryLeakEvent
            {
                timestamp = Time.time,
                leakType = "突发内存泄漏",
                memoryBefore = previous.totalAllocated,
                memoryAfter = current.totalAllocated,
                leakSize = growth,
                sceneName = current.sceneName,
                description = $"单帧内存暴涨: +{growthMB:F1}MB",
                severity = GetSeverity(growth)
            };
            
            AddSuspectedObjectsToLeak(leak);
            detectedLeaks.Add(leak);
        }
    }
    
    private void DetectTextureLeakEnhanced(MemorySample current)
    {
        if (samples.Count < 60) return;
        
        var oldSample = samples[samples.Count - 60];
        long texGrowth = current.textureMemory - oldSample.textureMemory;
        float texGrowthMB = texGrowth / (1024f * 1024f);
        
        if (texGrowthMB > 100f)
        {
            var leak = new MemoryLeakEvent
            {
                timestamp = Time.time,
                leakType = "纹理内存泄漏",
                memoryBefore = oldSample.textureMemory,
                memoryAfter = current.textureMemory,
                leakSize = texGrowth,
                sceneName = current.sceneName,
                description = $"纹理内存异常增长: +{texGrowthMB:F1}MB (数量: {oldSample.textureCount}→{current.textureCount})",
                severity = GetSeverity(texGrowth)
            };
            
            var largeTextures = currentSnapshot.Values
                .Where(s => s.objectType.Contains("Texture") && s.memorySize > 10 * 1024 * 1024)
                .OrderByDescending(s => s.memorySize)
                .Take(10);
            
            foreach (var tex in largeTextures)
            {
                leak.suspectedObjects.Add($"{tex.objectName} ({tex.memorySize / (1024 * 1024)}MB) - {tex.loadSource}");
            }
            
            detectedLeaks.Add(leak);
        }
    }
    
    private void DetectGameObjectLeakEnhanced(MemorySample current)
    {
        if (samples.Count < 60) return;
        
        var oldSample = samples[samples.Count - 60];
        int goGrowth = current.gameObjectCount - oldSample.gameObjectCount;
        
        if (goGrowth > 1000)
        {
            var leak = new MemoryLeakEvent
            {
                timestamp = Time.time,
                leakType = "GameObject泄漏",
                memoryBefore = oldSample.totalAllocated,
                memoryAfter = current.totalAllocated,
                leakSize = current.totalAllocated - oldSample.totalAllocated,
                sceneName = current.sceneName,
                description = $"GameObject数量异常增长: {oldSample.gameObjectCount} → {current.gameObjectCount} (+{goGrowth})",
                severity = MemoryLeakEvent.LeakSeverity.High
            };
            
            var gameObjects = FindObjectsOfType<GameObject>();
            var typeCount = new Dictionary<string, int>();
            
            foreach (var go in gameObjects)
            {
                if (go == null) continue;
                string typeName = go.name.Split('(')[0].Trim();
                
                if (typeCount.ContainsKey(typeName))
                    typeCount[typeName]++;
                else
                    typeCount[typeName] = 1;
            }
            
            foreach (var kvp in typeCount.OrderByDescending(k => k.Value).Take(5))
            {
                leak.suspectedObjects.Add($"{kvp.Key}: {kvp.Value}个实例");
            }
            
            detectedLeaks.Add(leak);
        }
    }
    
    private void AddSuspectedObjectsToLeak(MemoryLeakEvent leak)
    {
        var topLeaked = leakedObjects.Take(5);
        foreach (var obj in topLeaked)
        {
            leak.suspectedObjects.Add($"{obj.snapshot.objectType}: {obj.snapshot.objectName} " +
                                     $"({obj.snapshot.memorySize / (1024 * 1024)}MB) - {obj.leakReason}");
        }
    }
    
    private MemoryLeakEvent.LeakSeverity GetSeverity(long bytes)
    {
        float mb = bytes / (1024f * 1024f);
        if (mb > 200f) return MemoryLeakEvent.LeakSeverity.Critical;
        if (mb > 100f) return MemoryLeakEvent.LeakSeverity.High;
        if (mb > 50f) return MemoryLeakEvent.LeakSeverity.Medium;
        return MemoryLeakEvent.LeakSeverity.Low;
    }
    
    #endregion
    
    #region 场景监控
    
    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (!sceneProfiles.ContainsKey(scene.name))
        {
            sceneProfiles[scene.name] = new SceneMemoryProfile
            {
                sceneName = scene.name
            };
        }
        
        var profile = sceneProfiles[scene.name];
        profile.entryMemory = Profiler.GetTotalAllocatedMemoryLong();
        
        StartCoroutine(DelayedSceneMemoryCheck(scene.name));
    }
    
    private IEnumerator DelayedSceneMemoryCheck(string sceneName)
    {
        yield return new WaitForSeconds(1f);
        
        var currentMemory = Profiler.GetTotalAllocatedMemoryLong();
        var profile = sceneProfiles[sceneName];
        
        long growth = currentMemory - profile.entryMemory;
        float growthMB = growth / (1024f * 1024f);
        
        if (growthMB > 200f)
        {
            profile.warnings.Add($"场景加载后内存增长过大: {growthMB:F1}MB");
        }
        
        if (enableDeepTracking)
        {
            CaptureObjectSnapshot();
        }
    }
    
    private void OnSceneUnloaded(Scene scene)
    {
        if (sceneProfiles.ContainsKey(scene.name))
        {
            var profile = sceneProfiles[scene.name];
            profile.exitMemory = Profiler.GetTotalAllocatedMemoryLong();
            
            long memoryDrop = profile.entryMemory - profile.exitMemory;
            float dropMB = memoryDrop / (1024f * 1024f);
            
            if (dropMB < 50f && profile.entryMemory > 0)
            {
                profile.warnings.Add($"场景卸载后内存未明显下降: {dropMB:F1}MB");
            }
        }
        
        StartCoroutine(DelayedUnloadCheck(scene.name));
    }
    
    private IEnumerator DelayedUnloadCheck(string sceneName)
    {
        yield return new WaitForSeconds(2f);
        
        if (enableDeepTracking)
        {
            CaptureObjectSnapshot();
            
            var residualObjects = currentSnapshot.Values
                .Where(s => s.sceneName == sceneName && !s.isDontDestroyOnLoad)
                .ToList();
            
            if (residualObjects.Count > 0)
            {
                Debug.LogError($"<color=red>【场景泄漏】{sceneName} 卸载后残留 {residualObjects.Count} 个对象</color>");
            }
        }
    }
    
    #endregion
    
    #region 智能问题分析
    
    private List<ProblemAnalysis> AnalyzeProblems()
    {
        var problems = new List<ProblemAnalysis>();
        
        AnalyzeSceneUnloadProblems(problems);
        AnalyzeTextureLeakProblems(problems);
        AnalyzeGameObjectLeakProblems(problems);
        AnalyzeContinuousGrowthProblems(problems);
        AnalyzeResourceLoadingProblems(problems);
        
        return problems;
    }
    
    private void AnalyzeSceneUnloadProblems(List<ProblemAnalysis> problems)
    {
        foreach (var profile in sceneProfiles.Values)
        {
            if (profile.exitMemory > 0 && profile.entryMemory > 0)
            {
                long released = profile.entryMemory - profile.exitMemory;
                float releaseRate = (float)released / profile.entryMemory;
                
                if (releaseRate < 0.5f)
                {
                    var problem = new ProblemAnalysis
                    {
                        category = "场景资源未正确卸载",
                        responsibility = "程序组",
                        severity = "P0-紧急",
                        memoryImpact = (profile.entryMemory - released) / (1024 * 1024),
                        estimatedDays = 3
                    };
                    
                    problem.specificIssues.Add($"场景 {profile.sceneName} 卸载后仅释放 {released / (1024 * 1024)}MB ({releaseRate * 100:F1}%)");
                    problem.specificIssues.Add($"应释放约 {profile.entryMemory / (1024 * 1024)}MB，实际仅释放 {released / (1024 * 1024)}MB");
                    
                    problem.rootCauses.Add("场景卸载时未调用 Resources.UnloadUnusedAssets()");
                    problem.rootCauses.Add("静态引用持有场景资源");
                    problem.rootCauses.Add("事件订阅未取消");
                    problem.rootCauses.Add("DontDestroyOnLoad对象持有场景引用");
                    
                    problem.solutions.Add("在SceneManager中实现场景切换清理流程");
                    problem.solutions.Add("场景卸载时调用 Resources.UnloadUnusedAssets() + GC.Collect()");
                    problem.solutions.Add("检查所有静态变量和单例，确保场景切换时清空引用");
                    problem.solutions.Add("使用事件管理器统一管理订阅");
                    problem.solutions.Add("使用Memory Profiler定位具体未释放的对象");
                    
                    problems.Add(problem);
                }
            }
        }
    }
    
    private void AnalyzeTextureLeakProblems(List<ProblemAnalysis> problems)
    {
        var textureLeaks = detectedLeaks.Where(l => l.leakType == "纹理内存泄漏").ToList();
        
        if (textureLeaks.Count > 0)
        {
            long totalTextureLeak = textureLeaks.Sum(l => l.leakSize);
            var leakedTextures = leakedObjects.Where(l => l.snapshot.objectType.Contains("Texture")).ToList();
            
            bool isProgramIssue = false;
            bool isArtIssue = false;
            
            var resourcesTextures = leakedTextures.Where(t => t.snapshot.loadSource == "Resources").ToList();
            if (resourcesTextures.Count > leakedTextures.Count * 0.6f)
            {
                isProgramIssue = true;
            }
            
            var largeTextures = leakedTextures.Where(t => t.snapshot.memorySize > 20 * 1024 * 1024).ToList();
            if (largeTextures.Count > 0)
            {
                isArtIssue = true;
            }
            
            if (isProgramIssue || resourcesTextures.Count > 0)
            {
                var problem = new ProblemAnalysis
                {
                    category = "纹理资源加载后未卸载",
                    responsibility = "程序组",
                    severity = totalTextureLeak > 300 * 1024 * 1024 ? "P0-紧急" : "P1-重要",
                    memoryImpact = totalTextureLeak / (1024 * 1024),
                    estimatedDays = 5
                };
                
                problem.specificIssues.Add($"检测到 {textureLeaks.Count} 次纹理泄漏，总计 {totalTextureLeak / (1024 * 1024)}MB");
                problem.specificIssues.Add($"泄漏纹理对象数: {leakedTextures.Count}");
                
                if (resourcesTextures.Count > 0)
                {
                    problem.specificIssues.Add($"其中 {resourcesTextures.Count} 个来自Resources加载");
                    
                    foreach (var tex in resourcesTextures.Take(5))
                    {
                        problem.specificIssues.Add($"  - {tex.snapshot.objectName} ({tex.snapshot.memorySize / (1024 * 1024)}MB)");
                    }
                }
                
                problem.rootCauses.Add("Resources.Load() 后未调用对应的 UnloadAsset()");
                problem.rootCauses.Add("RenderTexture创建后未Release");
                problem.rootCauses.Add("UI图片引用未清空");
                problem.rootCauses.Add("缺少资源引用计数管理");
                
                problem.solutions.Add("实现ResourceManager，为所有资源加载添加引用计数");
                problem.solutions.Add("场景切换时强制卸载：Resources.UnloadUnusedAssets()");
                problem.solutions.Add("RenderTexture使用管理器统一管理生命周期");
                problem.solutions.Add("UI图片使用后及时清空sprite引用");
                problem.solutions.Add("替换为Addressables资源管理系统");
                
                problems.Add(problem);
            }
            
            if (isArtIssue)
            {
                var problem = new ProblemAnalysis
                {
                    category = "纹理规格过大或未压缩",
                    responsibility = "美术组 + TA",
                    severity = "P1-重要",
                    memoryImpact = largeTextures.Sum(t => t.snapshot.memorySize) / (1024 * 1024),
                    estimatedDays = 7
                };
                
                problem.specificIssues.Add($"发现 {largeTextures.Count} 个超大纹理（>20MB）");
                
                foreach (var tex in largeTextures.Take(5))
                {
                    problem.specificIssues.Add($"  - {tex.snapshot.objectName} ({tex.snapshot.memorySize / (1024 * 1024)}MB)");
                }
                
                problem.rootCauses.Add("纹理未启用压缩或压缩率过低");
                problem.rootCauses.Add("纹理尺寸超过2K");
                problem.rootCauses.Add("误开启 Read/Write Enabled（双倍内存）");
                problem.rootCauses.Add("UI纹理未使用Sprite Atlas打图集");
                
                problem.solutions.Add("所有纹理启用压缩：Android使用ASTC 6x6，iOS使用ASTC 6x6");
                problem.solutions.Add("纹理尺寸限制：UI最大1024，角色最大2048，场景最大2048");
                problem.solutions.Add("检查并关闭所有不必要的 Read/Write Enabled");
                problem.solutions.Add("UI纹理打入Sprite Atlas");
                problem.solutions.Add("使用编辑器工具批量优化纹理导入设置");
                
                problems.Add(problem);
            }
        }
    }
    
    private void AnalyzeGameObjectLeakProblems(List<ProblemAnalysis> problems)
    {
        var goLeaks = detectedLeaks.Where(l => l.leakType == "GameObject泄漏").ToList();
        
        if (goLeaks.Count > 0)
        {
            var problem = new ProblemAnalysis
            {
                category = "GameObject未及时销毁",
                responsibility = "程序组",
                severity = "P1-重要",
                memoryImpact = goLeaks.Sum(l => l.leakSize) / (1024 * 1024),
                estimatedDays = 4
            };
            
            problem.specificIssues.Add($"检测到 {goLeaks.Count} 次GameObject泄漏");
            
            var leakedGOs = leakedObjects.Where(l => l.snapshot.objectType == "GameObject").ToList();
            problem.specificIssues.Add($"泄漏GameObject对象数: {leakedGOs.Count}");
            
            var goTypes = new Dictionary<string, int>();
            foreach (var go in leakedGOs)
            {
                string typeName = go.snapshot.objectName.Split('(')[0].Trim();
                if (goTypes.ContainsKey(typeName))
                    goTypes[typeName]++;
                else
                    goTypes[typeName] = 1;
            }
            
            foreach (var kvp in goTypes.OrderByDescending(k => k.Value).Take(5))
            {
                problem.specificIssues.Add($"  - {kvp.Key}: {kvp.Value}个实例");
            }
            
            problem.rootCauses.Add("Instantiate后未及时Destroy");
            problem.rootCauses.Add("对象池回收逻辑缺失");
            problem.rootCauses.Add("特效播放完毕后未自动销毁");
            problem.rootCauses.Add("DontDestroyOnLoad对象累积");
            problem.rootCauses.Add("协程持有GameObject引用");
            
            problem.solutions.Add("实现通用对象池系统");
            problem.solutions.Add("特效添加自动销毁组件");
            problem.solutions.Add("定期清理DontDestroyOnLoad中的无用对象");
            problem.solutions.Add("使用weak reference避免强引用");
            problem.solutions.Add("场景切换时检查GameObject数量");
            
            problems.Add(problem);
        }
    }
    
    private void AnalyzeContinuousGrowthProblems(List<ProblemAnalysis> problems)
    {
        var continuousLeaks = detectedLeaks.Where(l => l.leakType == "持续内存增长").ToList();
        
        if (continuousLeaks.Count > 0)
        {
            var problem = new ProblemAnalysis
            {
                category = "事件订阅或静态引用泄漏",
                responsibility = "程序组",
                severity = "P0-紧急",
                memoryImpact = continuousLeaks.Sum(l => l.leakSize) / (1024 * 1024),
                estimatedDays = 10
            };
            
            if (samples.Count >= 60)
            {
                var recentSamples = samples.Skip(samples.Count - 60).ToList();
                float duration = recentSamples.Last().timestamp - recentSamples.First().timestamp;
                long growth = recentSamples.Last().totalAllocated - recentSamples.First().totalAllocated;
                float growthRate = (growth / (1024f * 1024f)) / (duration / 60f);
                
                problem.specificIssues.Add($"持续内存增长率: {growthRate:F2}MB/分钟");
                problem.specificIssues.Add($"预计1小时泄漏: {growthRate * 60:F0}MB");
            }
            
            problem.specificIssues.Add($"检测到 {continuousLeaks.Count} 次持续增长事件");
            
            problem.rootCauses.Add("静态事件订阅后未取消订阅");
            problem.rootCauses.Add("静态List/Dictionary持有对象引用");
            problem.rootCauses.Add("单例模式持有场景对象引用");
            problem.rootCauses.Add("委托回调未移除");
            problem.rootCauses.Add("协程泄漏");
            
            problem.solutions.Add("代码审查：所有事件订阅必须在OnDestroy中取消");
            problem.solutions.Add("实现EventManager统一管理事件订阅");
            problem.solutions.Add("静态集合在场景切换时调用Clear()");
            problem.solutions.Add("单例提供ClearSceneReferences()方法");
            problem.solutions.Add("使用weak reference避免强引用");
            problem.solutions.Add("协程使用时保存引用，及时StopCoroutine");
            
            problems.Add(problem);
        }
    }
    
    private void AnalyzeResourceLoadingProblems(List<ProblemAnalysis> problems)
    {
        var resourcesObjects = leakedObjects
            .Where(l => l.snapshot.loadSource == "Resources")
            .ToList();
        
        if (resourcesObjects.Count > 20)
        {
            var problem = new ProblemAnalysis
            {
                category = "Resources资源管理混乱",
                responsibility = "程序组",
                severity = "P1-重要",
                memoryImpact = resourcesObjects.Sum(o => o.snapshot.memorySize) / (1024 * 1024),
                estimatedDays = 14
            };
            
            problem.specificIssues.Add($"发现 {resourcesObjects.Count} 个Resources加载的泄漏对象");
            problem.specificIssues.Add($"总内存占用: {resourcesObjects.Sum(o => o.snapshot.memorySize) / (1024 * 1024)}MB");
            
            var typeGroups = resourcesObjects.GroupBy(o => o.snapshot.objectType);
            foreach (var group in typeGroups.OrderByDescending(g => g.Sum(o => o.snapshot.memorySize)).Take(3))
            {
                problem.specificIssues.Add($"  - {group.Key}: {group.Count()}个, {group.Sum(o => o.snapshot.memorySize) / (1024 * 1024)}MB");
            }
            
            problem.rootCauses.Add("缺少统一的资源管理系统");
            problem.rootCauses.Add("Resources.Load分散在各个脚本中");
            problem.rootCauses.Add("没有引用计数");
            problem.rootCauses.Add("重复加载同一资源");
            
            problem.solutions.Add("实现ResourceManager统一管理所有Resources加载");
            problem.solutions.Add("为每个资源添加引用计数");
            problem.solutions.Add("禁止直接使用Resources.Load");
            problem.solutions.Add("长期方案：迁移到Addressables");
            problem.solutions.Add("定期自动卸载长时间未使用的资源");
            
            problems.Add(problem);
        }
    }
    
    #endregion
    
    #region UI绘制
    
    private void DrawMonitorWindow(int windowID)
    {
        GUILayout.BeginVertical();
        
        GUILayout.Label($"<b>运行: {totalRunTime:F0}秒 | 样本: {samples.Count} | 泄漏: {leakedObjects.Count}</b>");
        GUILayout.Label($"<b>F9-UI | F10-报告 | F11-GC | F12-导出</b>", GUI.skin.box);
        
        GUILayout.Space(5);
        
        GUILayout.BeginHorizontal();
        if (GUILayout.Toggle(selectedTab == 0, "总览", GUI.skin.button)) selectedTab = 0;
        if (GUILayout.Toggle(selectedTab == 1, $"泄漏({leakedObjects.Count})", GUI.skin.button)) selectedTab = 1;
        if (GUILayout.Toggle(selectedTab == 2, "场景", GUI.skin.button)) selectedTab = 2;
        GUILayout.EndHorizontal();
        
        GUILayout.Space(5);
        
        scrollPosition = GUILayout.BeginScrollView(scrollPosition, GUILayout.Height(500));
        
        switch (selectedTab)
        {
            case 0:
                DrawOverviewTab();
                break;
            case 1:
                DrawLeakedObjectsTab();
                break;
            case 2:
                DrawSceneAnalysisTab();
                break;
        }
        
        GUILayout.EndScrollView();
        
        GUILayout.Space(5);
        
        GUILayout.BeginHorizontal();
        
        if (GUILayout.Button("生成报告"))
        {
            GenerateDetailedReport();
        }
        
        if (GUILayout.Button("强制GC"))
        {
            ForceGarbageCollection();
        }
        
        if (GUILayout.Button("导出泄漏"))
        {
            DumpLeakedObjects();
        }
        
        if (GUILayout.Button("清空"))
        {
            samples.Clear();
            detectedLeaks.Clear();
            leakedObjects.Clear();
        }
        
        GUILayout.EndHorizontal();
        
        GUILayout.EndVertical();
        
        GUI.DragWindow();
    }
    
    private void DrawOverviewTab()
    {
        if (samples.Count == 0) return;
        
        var current = samples.Last();
        
        GUILayout.Label("<b>当前状态</b>");
        GUILayout.BeginVertical(GUI.skin.box);
        
        GUILayout.Label($"总内存: {current.GetTotalMB()}MB / 峰值: {peakMemory / (1024 * 1024)}MB");
        GUILayout.Label($"纹理: {current.textureMemory / (1024 * 1024)}MB ({current.textureCount}个)");
        GUILayout.Label($"GameObject: {current.gameObjectCount}");
        GUILayout.Label($"FPS: {current.fps:F1} | 场景: {current.sceneName}");
        
        if (samples.Count >= 60)
        {
            var old = samples[samples.Count - 60];
            float duration = current.timestamp - old.timestamp;
            long growth = current.totalAllocated - old.totalAllocated;
            float growthRate = (growth / (1024f * 1024f)) / (duration / 60f);
            
            Color color = growthRate > leakRateThreshold ? Color.red : Color.green;
            GUI.color = color;
            GUILayout.Label($"<b>增长率: {growthRate:F2}MB/分</b>");
            GUI.color = Color.white;
        }
        
        GUILayout.EndVertical();
        
        GUILayout.Space(10);
        
        GUILayout.Label($"<b>泄漏警报 ({detectedLeaks.Count})</b>");
        
        foreach (var leak in detectedLeaks.OrderByDescending(l => l.timestamp).Take(5))
        {
            Color severityColor = leak.severity == MemoryLeakEvent.LeakSeverity.Critical ? Color.red :
                                 leak.severity == MemoryLeakEvent.LeakSeverity.High ? Color.yellow : Color.white;
            
            GUI.color = severityColor;
            GUILayout.BeginVertical(GUI.skin.box);
            GUI.color = Color.white;
            
            GUILayout.Label($"<b>[{leak.timestamp:F1}s] {leak.leakType}</b>");
            GUILayout.Label($"{leak.description}");
            
            if (leak.suspectedObjects.Count > 0)
            {
                GUILayout.Label("<b>可疑对象:</b>");
                foreach (var obj in leak.suspectedObjects.Take(2))
                {
                    GUILayout.Label($"  {obj}");
                }
            }
            
            GUILayout.EndVertical();
            GUILayout.Space(5);
        }
    }
    
    private void DrawLeakedObjectsTab()
    {
        GUILayout.Label($"<b>泄漏对象 (共{leakedObjects.Count}个)</b>");
        
        if (leakedObjects.Count == 0)
        {
            GUILayout.Label("暂未检测到泄漏对象");
            return;
        }
        
        foreach (var leak in leakedObjects.Take(20))
        {
            Color color = leak.snapshot.memorySize > 50 * 1024 * 1024 ? Color.red : 
                         leak.snapshot.memorySize > 10 * 1024 * 1024 ? Color.yellow : Color.white;
            
            GUI.color = color;
            GUILayout.BeginVertical(GUI.skin.box);
            GUI.color = Color.white;
            
            GUILayout.Label($"<b>{leak.snapshot.objectType}: {leak.snapshot.objectName}</b>");
            GUILayout.Label($"内存: {leak.snapshot.memorySize / (1024 * 1024)}MB");
            GUILayout.Label($"来源: {leak.snapshot.loadSource} | 存活: {leak.survivedSnapshots}");
            
            GUILayout.EndVertical();
            GUILayout.Space(5);
        }
    }
    
    private void DrawSceneAnalysisTab()
    {
        GUILayout.Label("<b>场景内存分析</b>");
        
        foreach (var profile in sceneProfiles.Values)
        {
            GUILayout.BeginVertical(GUI.skin.box);
            
            GUILayout.Label($"<b>{profile.sceneName}</b>");
            
            if (profile.entryMemory > 0)
            {
                GUILayout.Label($"进入: {profile.entryMemory / (1024 * 1024)}MB");
            }
            
            if (profile.exitMemory > 0)
            {
                long released = profile.entryMemory - profile.exitMemory;
                GUILayout.Label($"退出: {profile.exitMemory / (1024 * 1024)}MB");
                GUILayout.Label($"释放: {released / (1024 * 1024)}MB");
            }
            
            if (profile.warnings.Count > 0)
            {
                GUI.color = Color.yellow;
                GUILayout.Label("<b>警告:</b>");
                GUI.color = Color.white;
                
                foreach (var warning in profile.warnings)
                {
                    GUILayout.Label($"  {warning}");
                }
            }
            
            GUILayout.EndVertical();
            GUILayout.Space(5);
        }
    }
    
    #endregion
    
    #region 报告生成
    
    public void GenerateDetailedReport()
    {
        if (samples.Count == 0)
        {
            Debug.LogWarning("没有足够的数据生成报告");
            return;
        }
        
        StringBuilder report = new StringBuilder();
        
        report.AppendLine("==========================================");
        report.AppendLine("   Unity 内存泄漏检测报告");
        report.AppendLine("==========================================");
        report.AppendLine($"生成时间: {System.DateTime.Now:yyyy/MM/dd HH:mm:ss}");
        report.AppendLine($"运行时长: {totalRunTime:F1}秒");
        report.AppendLine($"采样数量: {samples.Count}");
        report.AppendLine();
        
        // 总体统计
        report.AppendLine("【总体统计】");
        report.AppendLine($"基准内存: {baselineSample.GetTotalMB()}MB");
        report.AppendLine($"当前内存: {samples.Last().GetTotalMB()}MB");
        report.AppendLine($"峰值内存: {peakMemory / (1024 * 1024)}MB");
        report.AppendLine($"总增长: {(samples.Last().totalAllocated - baselineSample.totalAllocated) / (1024 * 1024)}MB");
        
        if (totalRunTime > 60f)
        {
            float avgGrowthRate = ((samples.Last().totalAllocated - baselineSample.totalAllocated) / (1024f * 1024f)) / (totalRunTime / 60f);
            report.AppendLine($"平均增长率: {avgGrowthRate:F2}MB/分钟");
        }
        
        report.AppendLine();
        
        // 泄漏事件统计
        report.AppendLine($"【检测到 {detectedLeaks.Count} 个泄漏事件】");
        
        var criticalLeaks = detectedLeaks.Where(l => l.severity == MemoryLeakEvent.LeakSeverity.Critical).ToList();
        var highLeaks = detectedLeaks.Where(l => l.severity == MemoryLeakEvent.LeakSeverity.High).ToList();
        
        report.AppendLine($"严重: {criticalLeaks.Count} | 高危: {highLeaks.Count} | " +
                         $"中危: {detectedLeaks.Count(l => l.severity == MemoryLeakEvent.LeakSeverity.Medium)} | " +
                         $"低危: {detectedLeaks.Count(l => l.severity == MemoryLeakEvent.LeakSeverity.Low)}");
        report.AppendLine();
        
        // TOP 10泄漏事件
        foreach (var leak in detectedLeaks.OrderByDescending(l => l.leakSize).Take(10))
        {
            report.AppendLine($"[{leak.timestamp:F1}s] {leak.leakType} - {leak.severity}");
            report.AppendLine($"  描述: {leak.description}");
            report.AppendLine($"  场景: {leak.sceneName}");
            report.AppendLine($"  泄漏大小: {leak.leakSize / (1024 * 1024)}MB");
            
            if (leak.suspectedObjects.Count > 0)
            {
                report.AppendLine("  可疑对象:");
                foreach (var obj in leak.suspectedObjects)
                {
                    report.AppendLine($"    - {obj}");
                }
            }
            
            report.AppendLine();
        }
        
        // 场景分析
        report.AppendLine("【场景内存分析】");
        foreach (var profile in sceneProfiles.Values)
        {
            report.AppendLine($"场景: {profile.sceneName}");
            if (profile.entryMemory > 0)
            {
                report.AppendLine($"  进入内存: {profile.entryMemory / (1024 * 1024)}MB");
            }
            if (profile.exitMemory > 0)
            {
                report.AppendLine($"  退出内存: {profile.exitMemory / (1024 * 1024)}MB");
                report.AppendLine($"  释放内存: {(profile.entryMemory - profile.exitMemory) / (1024 * 1024)}MB");
            }
            
            if (profile.warnings.Count > 0)
            {
                report.AppendLine("  ⚠️ 警告:");
                foreach (var warning in profile.warnings)
                {
                    report.AppendLine($"    - {warning}");
                }
            }
            report.AppendLine();
        }
        
        // ========== 核心：问题定性与责任划分 ==========
        report.AppendLine("==========================================");
        report.AppendLine("【问题定性与责任划分】");
        report.AppendLine("==========================================");
        report.AppendLine();
        
        var problems = AnalyzeProblems();
        
        if (problems.Count == 0)
        {
            report.AppendLine("未检测到明确的内存问题");
        }
        else
        {
            // 按责任方分组统计
            var programProblems = problems.Where(p => p.responsibility.Contains("程序")).ToList();
            var artProblems = problems.Where(p => p.responsibility.Contains("美术")).ToList();
            
            long programImpact = programProblems.Sum(p => p.memoryImpact);
            long artImpact = artProblems.Sum(p => p.memoryImpact);
            long totalImpact = programImpact + artImpact;
            
            report.AppendLine("【责任统计】");
            report.AppendLine($"程序组问题: {programProblems.Count}个, 影响内存 {programImpact}MB ({(totalImpact > 0 ? programImpact * 100f / totalImpact : 0):F1}%)");
            report.AppendLine($"美术组问题: {artProblems.Count}个, 影响内存 {artImpact}MB ({(totalImpact > 0 ? artImpact * 100f / totalImpact : 0):F1}%)");
            report.AppendLine();
            
            // 详细问题列表
            int problemIndex = 1;
            foreach (var problem in problems.OrderBy(p => p.severity).ThenByDescending(p => p.memoryImpact))
            {
                report.AppendLine($"========== 问题 {problemIndex} ==========");
                report.AppendLine($"类别: {problem.category}");
                report.AppendLine($"责任方: {problem.responsibility}");
                report.AppendLine($"优先级: {problem.severity}");
                report.AppendLine($"内存影响: {problem.memoryImpact}MB");
                report.AppendLine($"预计修复时间: {problem.estimatedDays}天");
                report.AppendLine();
                
                if (problem.specificIssues.Count > 0)
                {
                    report.AppendLine("具体问题:");
                    foreach (var issue in problem.specificIssues)
                    {
                        report.AppendLine($"  - {issue}");
                    }
                    report.AppendLine();
                }
                
                if (problem.rootCauses.Count > 0)
                {
                    report.AppendLine("根本原因:");
                    foreach (var cause in problem.rootCauses)
                    {
                        report.AppendLine($"  - {cause}");
                    }
                    report.AppendLine();
                }
                
                if (problem.solutions.Count > 0)
                {
                    report.AppendLine("解决方案:");
                    foreach (var solution in problem.solutions)
                    {
                        report.AppendLine($"  - {solution}");
                    }
                    report.AppendLine();
                }
                
                report.AppendLine();
                
                problemIndex++;
            }
        }
        
        // 泄漏对象详情
        if (leakedObjects.Count > 0)
        {
            report.AppendLine("==========================================");
            report.AppendLine("【泄漏对象TOP 20】");
            report.AppendLine("==========================================");
            
            var topLeaks = leakedObjects.OrderByDescending(l => l.snapshot.memorySize).Take(20);
            foreach (var leak in topLeaks)
            {
                report.AppendLine($"{leak.snapshot.objectType}: {leak.snapshot.objectName}");
                report.AppendLine($"  内存: {leak.snapshot.memorySize / (1024 * 1024)}MB");
                report.AppendLine($"  来源: {leak.snapshot.loadSource}");
                report.AppendLine($"  场景: {leak.snapshot.sceneName}");
                report.AppendLine($"  存活: {leak.survivedSnapshots}个快照");
                report.AppendLine($"  原因: {leak.leakReason}");
                report.AppendLine();
            }
        }
        
        report.AppendLine("==========================================");
        
        string reportText = report.ToString();
        Debug.Log(reportText);
        
        // 保存到文件
        string filePath = $"{Application.persistentDataPath}/MemoryLeakReport_{System.DateTime.Now:yyyyMMdd_HHmmss}.txt";
        System.IO.File.WriteAllText(filePath, reportText);
        Debug.Log($"<color=cyan>【报告已保存】{filePath}</color>");
    }
    
    #endregion
    
    #region 导出泄漏对象
    
    private void DumpLeakedObjects()
    {
        if (leakedObjects.Count == 0)
        {
            Debug.LogWarning("没有检测到泄漏对象");
            return;
        }
        
        StringBuilder dump = new StringBuilder();
        
        dump.AppendLine("==========================================");
        dump.AppendLine("   泄漏对象详细信息");
        dump.AppendLine("==========================================");
        dump.AppendLine($"导出时间: {System.DateTime.Now:yyyy/MM/dd HH:mm:ss}");
        dump.AppendLine($"泄漏对象总数: {leakedObjects.Count}");
        dump.AppendLine($"总泄漏内存: {leakedObjects.Sum(l => l.snapshot.memorySize) / (1024 * 1024)}MB");
        dump.AppendLine();
        
        // 按类型分组
        var groupedByType = leakedObjects.GroupBy(l => l.snapshot.objectType);
        
        foreach (var group in groupedByType.OrderByDescending(g => g.Sum(l => l.snapshot.memorySize)))
        {
            dump.AppendLine($"【{group.Key}】- {group.Count()}个对象, {group.Sum(l => l.snapshot.memorySize) / (1024 * 1024)}MB");
            dump.AppendLine();
            
            foreach (var leak in group.OrderByDescending(l => l.snapshot.memorySize).Take(20))
            {
                dump.AppendLine($"  对象名: {leak.snapshot.objectName}");
                dump.AppendLine($"  内存: {leak.snapshot.memorySize / (1024 * 1024)}MB");
                dump.AppendLine($"  来源: {leak.snapshot.loadSource}");
                dump.AppendLine($"  场景: {leak.snapshot.sceneName}");
                dump.AppendLine($"  InstanceID: {leak.snapshot.instanceID}");
                dump.AppendLine($"  存活: {leak.survivedSnapshots}个快照");
                dump.AppendLine($"  原因: {leak.leakReason}");
                dump.AppendLine();
            }
        }
        
        dump.AppendLine("==========================================");
        
        string dumpText = dump.ToString();
        string filePath = $"{Application.persistentDataPath}/LeakedObjects_{System.DateTime.Now:yyyyMMdd_HHmmss}.txt";
        System.IO.File.WriteAllText(filePath, dumpText);
        
        Debug.Log($"<color=cyan>【泄漏对象已导出】{filePath}</color>");
    }
    
    #endregion
    
    #region 工具方法
    
    public void ForceGarbageCollection()
    {
        var before = Profiler.GetTotalAllocatedMemoryLong();
        
        Resources.UnloadUnusedAssets();
        System.GC.Collect();
        System.GC.WaitForPendingFinalizers();
        System.GC.Collect();
        
        var after = Profiler.GetTotalAllocatedMemoryLong();
        long freed = before - after;
        
        Debug.Log($"<color=green>【强制GC】释放了 {freed / (1024 * 1024)}MB 内存</color>");
        
        if (enableDeepTracking)
        {
            CaptureObjectSnapshot();
        }
    }
    
    public void PauseMonitoring()
    {
        isMonitoring = false;
        Debug.Log("<color=yellow>【监控已暂停】</color>");
    }
    
    public void ResumeMonitoring()
    {
        isMonitoring = true;
        Debug.Log("<color=green>【监控已恢复】</color>");
    }
    
    #endregion
}
