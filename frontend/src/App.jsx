
import { useEffect, useState, useRef } from "react";
import {
  LayoutDashboard, Camera, Users, PawPrint, Video,
  Bell, Search, ShieldCheck, Activity, Settings,
  Menu, CircleAlert, Clock, ChevronRight,
  Mic, MicOff, Volume2, VolumeX
} from "lucide-react";


const navigation = [
  { name: "Dashboard", icon: LayoutDashboard },
  { name: "Live Monitoring", icon: Camera },
  { name: "Person Records", icon: Users },
  { name: "Animal Detection", icon: PawPrint },
  { name: "Video Recordings", icon: Video },
  { name: "Alerts", icon: Bell },
  { name: "Settings", icon: Settings },
];

function App() {
  const [apiStats, setApiStats] = useState({
    object_counts: [],
    category_counts: [],
    unknown_person_count: 0
  });
  const [recentEvents, setRecentEvents] = useState([]);
  const [videoCount, setVideoCount] = useState(0);
  const [persons, setPersons] = useState([]);
  const [personLoading, setPersonLoading] = useState(false);
  const [personError, setPersonError] = useState("");
  const [adminCredentials, setAdminCredentials] = useState(null);
  const [adminUsername, setAdminUsername] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  
  const [showAddPerson, setShowAddPerson] = useState(false);
  const [newPersonName, setNewPersonName] = useState("");
  const [cameraStream, setCameraStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState("");
  const [registrationLoading, setRegistrationLoading] = useState(false);
  const videoRef = useRef(null);




const [apiStatus, setApiStatus] = useState("Connecting...");

useEffect(() => {
  const fetchDashboardData = async () => {
    try {
      const [statsResponse, eventsResponse, videosResponse] =
        await Promise.all([
          fetch("http://127.0.0.1:8000/api/statistics"),
          fetch("http://127.0.0.1:8000/api/events?limit=5"),
          fetch("http://127.0.0.1:8000/api/videos")
        ]);

      if (!statsResponse.ok || !eventsResponse.ok || !videosResponse.ok) {
        throw new Error("Failed to fetch dashboard data");
      }

      const [statsData, eventsData, videosData] = await Promise.all([
        statsResponse.json(),
        eventsResponse.json(),
        videosResponse.json()
      ]);

      setApiStats(statsData);
      setRecentEvents(eventsData.events);
      setVideoCount(videosData.total_videos);
      setApiStatus("Connected");

    } catch (error) {
      console.error("Dashboard API error:", error);
      setApiStatus("Disconnected");
    }
  };

  fetchDashboardData();

  const interval = setInterval(fetchDashboardData, 10000);

  return () => clearInterval(interval);
}, []);

const loadPersons = async (credentials = adminCredentials) => {
  if (!credentials) {
    setPersonError("Administrator login is required.");
    return;
  }

  setPersonLoading(true);
  setPersonError("");

  try {
    const token = btoa(
      `${credentials.username}:${credentials.password}`
    );

    const response = await fetch(
      "http://127.0.0.1:8000/api/persons",
      {
        headers: {
          Authorization: `Basic ${token}`
        }
      }
    );

    if (response.status === 401) {
      setAdminCredentials(null);
      throw new Error("Invalid administrator credentials.");
    }

    if (!response.ok) {
      throw new Error("Unable to load authorized persons.");
    }

    const data = await response.json();
    setPersons(data.persons || []);

  } catch (error) {
    setPersonError(error.message);
  } finally {
    setPersonLoading(false);
  }
};


const handleAdminLogin = async (e) => {
  e.preventDefault();

  const credentials = {
    username: adminUsername.trim(),
    password: adminPassword
  };

  setAdminCredentials(credentials);

  await loadPersons(credentials);

  setAdminPassword("");
};

const startCamera = async () => {
  try {
    setPersonError("");

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false
    });

    setCameraStream(stream);
    setCapturedImage("");
  } catch (error) {
    setPersonError(
      "Unable to access camera. Please allow camera permission."
    );
  }
};

const stopCamera = () => {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
  }

  setCameraStream(null);
};

const captureFace = () => {
  if (!videoRef.current) return;

  const video = videoRef.current;

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const context = canvas.getContext("2d");
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  setCapturedImage(canvas.toDataURL("image/jpeg"));
  stopCamera();
};
useEffect(() => {
  if (videoRef.current && cameraStream) {
    videoRef.current.srcObject = cameraStream;
  }

  return () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
    }
  };
}, [cameraStream]);

const registerPerson = async () => {
  if (!newPersonName.trim()) {
    setPersonError("Please enter the person's name.");
    return;
  }

  if (!capturedImage) {
    setPersonError("Please capture a face image first.");
    return;
  }

  setRegistrationLoading(true);
  setPersonError("");

  try {
    const token = btoa(
      `${adminCredentials.username}:${adminCredentials.password}`
    );

    const response = await fetch("http://127.0.0.1:8000/api/persons", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Basic ${token}`
      },
      body: JSON.stringify({
        person_name: newPersonName.trim(),
        image: capturedImage
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Registration failed.");
    }

    alert(data.message);

    setNewPersonName("");
    setCapturedImage("");
    setShowAddPerson(false);

    await loadPersons(adminCredentials);

  } catch (error) {
    setPersonError(error.message);
  } finally {
    setRegistrationLoading(false);
  }
};


const getCategoryCount = (category) => {
  const item = apiStats.category_counts.find(
    (item) => item.category?.toLowerCase() === category.toLowerCase()
  );

  return item ? item.total : 0;
};

const stats = [
  {
    title: "Total Person Events",
    value: getCategoryCount("person"),
    icon: Users,
    color: "#6366f1"
  },
  {
    title: "Animal Detections",
    value: getCategoryCount("animal"),
    icon: PawPrint,
    color: "#16a34a"
  },
  {
    title: "Unknown Person Events",
    value: apiStats.unknown_person_count,
    icon: CircleAlert,
    color: "#ef4444"
  },
  {
    title: "Video Recordings",
    value: videoCount,
    icon: Video,
    color: "#d97706"
  },
];
  const [active, setActive] = useState("Dashboard");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
const [isSpeaking, setIsSpeaking] = useState(false);
const [voiceStatus, setVoiceStatus] = useState("");

const recognitionRef = useRef(null);

// Start voice input
const startListening = () => {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    setVoiceStatus("Voice input is not supported by this browser.");
    return;
  }

  const recognition = new SpeechRecognition();

  recognition.lang = "en-IN";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    setIsListening(true);
    setVoiceStatus("Listening...");
  };

  recognition.onresult = (event) => {
    const spokenText = event.results[0][0].transcript;
    setQuestion(spokenText);
    setVoiceStatus("Voice input received!");
  };

  recognition.onerror = () => {
    setVoiceStatus("Could not recognize your voice. Try again.");
  };

  recognition.onend = () => {
    setIsListening(false);
  };

  recognitionRef.current = recognition;
  recognition.start();
};

// Stop voice input
const stopListening = () => {
  recognitionRef.current?.stop();
  setIsListening(false);
};

// Speak the assistant's response
const speakText = (text) => {
  if (!("speechSynthesis" in window)) {
    setVoiceStatus("Voice output is not supported.");
    return;
  }

  window.speechSynthesis.cancel();

  const speech = new SpeechSynthesisUtterance(text);
  speech.lang = "en-IN";
  speech.rate = 1;

  speech.onstart = () => setIsSpeaking(true);
  speech.onend = () => setIsSpeaking(false);
  speech.onerror = () => setIsSpeaking(false);

  window.speechSynthesis.speak(speech);
};

// Stop speaking
const stopSpeaking = () => {
  window.speechSynthesis.cancel();
  setIsSpeaking(false);
};

  const askAssistant = async () => {
    const userQuestion = question.trim();

    if (!userQuestion) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userQuestion }
    ]);
    
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/query",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: userQuestion,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to get a response from the server.");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer }
      ]);

    } catch (error) {
      console.error("NLP API error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Unable to connect to the assistant. Please check whether the backend server is running."
        }
      ]);

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Inter, Arial, sans-serif; background: #f4f6fb; color: #172033; }
        .app { min-height: 100vh; display: flex; }
        .sidebar { width: 250px; background: #111827; color: white; padding: 25px 16px; flex-shrink: 0; }
        .brand { display: flex; align-items: center; gap: 12px; padding: 0 10px 30px; }
        .brand-icon { background: #4f46e5; padding: 10px; border-radius: 10px; display: flex; }
        .brand h2 { font-size: 17px; margin: 0; }
        .brand small { color: #9ca3af; font-size: 11px; }
        .nav-label { color: #6b7280; font-size: 11px; padding: 10px; text-transform: uppercase; letter-spacing: 1px; }
        .nav-item { display: flex; align-items: center; gap: 13px; padding: 13px 12px; margin: 5px 0; border-radius: 8px; color: #cbd5e1; cursor: pointer; font-size: 14px; }
        .nav-item:hover, .nav-item.active { background: #312e81; color: white; }
        .main { flex: 1; min-width: 0; }
        .topbar { height: 75px; background: white; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; }
        .topbar h3 { margin: 0; font-size: 17px; }
        .top-actions { display: flex; align-items: center; gap: 20px; color: #64748b; }
        .admin { display: flex; align-items: center; gap: 10px; font-size: 13px; }
        .avatar { width: 35px; height: 35px; background: #e0e7ff; color: #4338ca; border-radius: 50%; display: grid; place-items: center; font-weight: bold; }
        .content { padding: 30px 32px; max-width: 1500px; margin: auto; }
        .welcome { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; gap: 12px; }
        .welcome h1 { font-size: 25px; margin: 0 0 7px; }
        .muted { color: #8490a3; font-size: 13px; }
        .status { background: #dcfce7; color: #15803d; padding: 9px 13px; border-radius: 20px; font-size: 12px; display: flex; align-items: center; gap: 7px; }
        .dot { width: 7px; height: 7px; background: #16a34a; border-radius: 50%; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 25px; }
        .card { background: white; border: 1px solid #e9edf4; border-radius: 12px; padding: 21px; }
        .stat-top { display: flex; justify-content: space-between; align-items: center; }
        .stat-icon { padding: 11px; border-radius: 10px; }
        .stat-value { font-size: 27px; font-weight: 700; margin: 18px 0 5px; }
        .section-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px; margin-bottom: 22px; }
        .section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .section-title h3 { font-size: 16px; margin: 0; }
        .link { color: #4f46e5; font-size: 12px; cursor: pointer; }
        .monitor { height: 235px; background: #111827; border-radius: 9px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9ca3af; gap: 12px; text-align: center; }
        .monitor p { margin: 0; font-size: 13px; }
        .monitor small { font-size: 11px; color: #64748b; }
        .alert { display: flex; gap: 12px; padding: 13px 0; border-bottom: 1px solid #eef0f4; }
        .alert:last-child { border: 0; }
        .alert-icon { padding: 9px; height: fit-content; border-radius: 9px; background: #fee2e2; color: #dc2626; }
        .alert strong { font-size: 13px; }
        .alert p { margin: 5px 0; font-size: 12px; color: #8490a3; }
        .query-box { display: flex; gap: 10px; margin-top: 14px; }
        .query-box input { flex: 1; min-width: 0; padding: 12px; border: 1px solid #dce1eb; border-radius: 8px; outline: none; }
        .query-box button { border: 0; background: #4f46e5; color: white; padding: 0 18px; border-radius: 8px; cursor: pointer; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
        th { color: #8490a3; font-weight: 500; padding: 12px; border-bottom: 1px solid #edf0f5; }
        td { padding: 14px 12px; border-bottom: 1px solid #f0f2f6; }
        .tag { padding: 5px 9px; border-radius: 15px; font-size: 11px; background: #dcfce7; color: #15803d; }
        @media(max-width: 1000px) { .stats { grid-template-columns: repeat(2, 1fr); } .section-grid { grid-template-columns: 1fr; } }
        @media(max-width: 650px) { .sidebar { width: 65px; padding: 20px 8px; } .brand { padding: 0 7px 25px; } .brand h2, .brand small, .nav-item span, .nav-label { display: none; } .nav-item { justify-content: center; padding: 13px 5px; } .content { padding: 20px 13px; } .topbar { padding: 0 15px; } .stats { gap: 10px; } .card { padding: 14px; } .welcome h1 { font-size: 20px; } }
      `}</style>

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={25} /></div>
          <div><h2>Smart Surveillance</h2><small>Intelligent Security System</small></div>
        </div>

        <div className="nav-label">Main Menu</div>
        {navigation.map(({ name, icon: Icon }) => (
          <div key={name} className={`nav-item ${active === name ? "active" : ""}`} onClick={() => setActive(name)}>
            <Icon size={19} /><span>{name}</span>
          </div>
        ))}
      </aside>

      <main className="main">
        <header className="topbar">
          <h3>{active}</h3>
          <div className="top-actions">
            <Bell size={19} />
            <div className="admin"><div className="avatar">A</div><span>Administrator</span></div>
          </div>
        </header>

        <div className="content">
          {active === "Dashboard" && (
            <>
          <div className="welcome">
            <div><h1>Surveillance Overview</h1><div className="muted">Monitor activity and security events from one place.</div></div>
            <div
              className="status"
              style={{
                background:
                  apiStatus === "Connected" ? "#dcfce7" :
                  apiStatus === "Disconnected" ? "#fee2e2" : "#fef3c7",

                color:
                  apiStatus === "Connected" ? "#15803d" :
                  apiStatus === "Disconnected" ? "#b91c1c" : "#92400e"
              }}
            >
              <span
                className="dot"
                style={{
                  background:
                    apiStatus === "Connected" ? "#16a34a" :
                    apiStatus === "Disconnected" ? "#dc2626" : "#d97706"
                }}
              ></span>

              {apiStatus === "Connected"
                ? "Backend Connected"
                : apiStatus === "Disconnected"
                  ? "Backend Disconnected"
                  : "Connecting..."}
            </div>
          </div>

          <div className="stats">
            {stats.map(({ title, value, icon: Icon, color }) => (
              <div className="card" key={title}>
                <div className="stat-top">
                  <span className="muted">{title}</span>
                  <div className="stat-icon" style={{ background: `${color}18`, color }}><Icon size={21} /></div>
                </div>
                <div className="stat-value">{value}</div>
                <div className="muted">Recorded in surveillance database</div>
              </div>
            ))}
          </div>

          <div className="section-grid">
            <section className="card">
              <div className="section-title"><h3><Camera size={17} style={{ verticalAlign: "middle", marginRight: 8 }} />Live Monitoring</h3><span className="link">Camera 01</span></div>
              <div className="monitor">
                <Camera size={38} />
                <p>Live camera feed will appear here</p>
                <small>Camera connection will be integrated in the next stage</small>
              </div>
            </section>

            <section className="card">
              <div className="section-title"><h3><Bell size={17} style={{ verticalAlign: "middle", marginRight: 8 }} />Recent Alerts</h3><span className="link">View all</span></div>
              <div className="alert">
                <div className="alert-icon"><CircleAlert size={18} /></div>
                <div><strong>Unknown person events</strong><p>Unknown-person events are recorded in the database.</p></div>
              </div>
              <div className="alert">
                <div className="alert-icon" style={{ background: "#fef3c7", color: "#d97706" }}><Activity size={18} /></div>
                <div><strong>Detection activity</strong><p>Surveillance detection records are available.</p></div>
              </div>
              <div className="alert">
                <div className="alert-icon" style={{ background: "#dcfce7", color: "#15803d" }}><ShieldCheck size={18} /></div>
                <div><strong>System status</strong><p>Dashboard interface is ready.</p></div>
              </div>
            </section>
          </div>

          <section className="card" style={{ marginBottom: 22 }}>
            <div className="section-title">
              <h3>
                <Activity size={17} style={{ verticalAlign: "middle", marginRight: 8 }} />
                Ask Surveillance Assistant
              </h3>
            </div>

            <div className="muted">
              Ask questions about people, animals, unknown visitors, events and recordings.
            </div>

            {/* CHAT MESSAGES */}
            <div style={{
              marginTop: 20,
              display: "flex",
              flexDirection: "column",
              gap: 14
            }}>
              {messages.map((message, index) => (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    justifyContent: message.role === "user" ? "flex-end" : "flex-start"
                  }}
                >
                  <div style={{
                    maxWidth: "75%",
                    padding: "13px 17px",
                    borderRadius: 14,
                    background: message.role === "user" ? "#4f46e5" : "#eef2ff",
                    color: message.role === "user" ? "white" : "#1e293b",
                    fontSize: 14,
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap"
                  }}>
                    <strong>
                      {message.role === "user" ? "You" : "Surveillance Assistant"}
                    </strong>
                    <div style={{ marginTop: 5 }}>{message.text}</div>
                    {message.role === "assistant" && (
                      <button
                        type="button"
                        onClick={() =>
                          isSpeaking ? stopSpeaking() : speakText(message.text)
                        }
                        title={isSpeaking ? "Stop speaking" : "Listen to this answer"}
                        style={{
                          marginTop: 10,
                          padding: "6px 10px",
                          background: "#e0e7ff",
                          color: "#4338ca",
                          border: "none",
                          borderRadius: 6,
                          cursor: "pointer"
                        }}
                      >
                        {isSpeaking ? <VolumeX size={17} /> : <Volume2 size={17} />}
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div style={{
                  alignSelf: "flex-start",
                  padding: 13,
                  background: "#eef2ff",
                  borderRadius: 12,
                  color: "#4f46e5",
                  fontSize: 13
                }}>
                  Assistant is thinking...
                </div>
              )}
            </div>

            {/* QUESTION INPUT AT THE BOTTOM */}
            <form
              className="query-box"
              onSubmit={(e) => {
                e.preventDefault();
                askAssistant();
              }}
            >
              <button
                type="button"
                onClick={isListening ? stopListening : startListening}
                disabled={loading}
                title={isListening ? "Stop listening" : "Speak your question"}
                style={{
                  background: isListening ? "#dc2626" : "#e0e7ff",
                  color: isListening ? "white" : "#4338ca",
                  padding: "0 14px"
                }}
              >
                {isListening ? <MicOff size={19} /> : <Mic size={19} />}
              </button>
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask anything about your surveillance system..."
                disabled={loading}
              />

              <button type="submit" disabled={loading}>
                {loading ? "Thinking..." : "Ask"}
              </button>
            </form>
            {voiceStatus && (
              <div
                style={{
                  marginTop: 8,
                  fontSize: 12,
                  color: "#6366f1"
                }}
              >
                {voiceStatus}
              </div>
            )}
          </section>

          <section className="card">
            <div className="section-title"><h3><Clock size={17} style={{ verticalAlign: "middle", marginRight: 8 }} />Recent Surveillance Events</h3><span className="link">View all <ChevronRight size={13} style={{ verticalAlign: "middle" }} /></span></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Event</th><th>Object</th><th>Camera</th><th>Status</th></tr></thead>
                <tbody>
                  {recentEvents.length > 0 ? (
                    recentEvents.map((event) => (
                      <tr key={event.event_id}>
                        <td>{event.event_type}</td>
                        <td>{event.object_type || "Unknown"}</td>
                        <td>{event.camera_id || "—"}</td>
                        <td>
                          <span className="tag">Recorded</span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4">No surveillance events found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
            </>
                    )}
          {active === "Person Records" && (
          <section className="card">
          <div className="section-title">
            <h3>
              <Users size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
              Authorized Persons
            </h3>

            {adminCredentials && (
              <button
                type="button"
                onClick={() => {
                  setShowAddPerson(true);
                  setPersonError("");
                }}
                style={{
                  padding: "9px 14px",
                  background: "#4f46e5",
                  color: "white",
                  border: "none",
                  borderRadius: 7,
                  cursor: "pointer"
                }}
              >
                + Add Person
              </button>
            )}
          </div>

              {!adminCredentials ? (
                <form
                  onSubmit={handleAdminLogin}
                  style={{
                    maxWidth: 400,
                    display: "flex",
                    flexDirection: "column",
                    gap: 14
                  }}
                >
                  <p className="muted">
                    Administrator login is required to access authorized person records.
                  </p>

                  <input
                    type="text"
                    placeholder="Administrator username"
                    value={adminUsername}
                    onChange={(e) => setAdminUsername(e.target.value)}
                    required
                    style={{
                      padding: 12,
                      border: "1px solid #dce1eb",
                      borderRadius: 8
                    }}
                  />

                  <input
                    type="password"
                    placeholder="Administrator password"
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    required
                    style={{
                      padding: 12,
                      border: "1px solid #dce1eb",
                      borderRadius: 8
                    }}
                  />

                  <button
                    type="submit"
                    disabled={personLoading}
                    style={{
                      padding: 12,
                      background: "#4f46e5",
                      color: "white",
                      border: "none",
                      borderRadius: 8,
                      cursor: "pointer"
                    }}
                  >
                    {personLoading ? "Signing in..." : "Administrator Login"}
                  </button>
                </form>
              ) : (
                <>
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 18
                  }}>
                    <div className="muted">
                      Total authorized persons: {persons.length}
                    </div>

                    <button
                      type="button"
                      onClick={() => loadPersons()}
                      disabled={personLoading}
                      style={{
                        padding: "9px 14px",
                        background: "#4f46e5",
                        color: "white",
                        border: "none",
                        borderRadius: 7,
                        cursor: "pointer"
                      }}
                    >
                      {personLoading ? "Loading..." : "Refresh"}
                    </button>
                  </div>

                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Person ID</th>
                          <th>Person Name</th>
                          <th>Registration Date</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {persons.length > 0 ? (
                          persons.map((person) => (
                            <tr key={person.person_id}>
                              <td>{person.person_id}</td>
                              <td>{person.person_name}</td>
                              <td>
                                {new Date(person.created_at).toLocaleString()}
                              </td>
                              <td>
                                <span className="tag">Authorized</span>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="4">
                              No authorized persons registered.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                                    {showAddPerson && (
                    <div style={{
                      marginTop: 25,
                      padding: 20,
                      border: "1px solid #e5e7eb",
                      borderRadius: 10
                    }}>
                      <h3>Register New Person</h3>

                      <input
                        type="text"
                        placeholder="Enter person's name"
                        value={newPersonName}
                        onChange={(e) => setNewPersonName(e.target.value)}
                        style={{
                          width: "100%",
                          padding: 12,
                          marginBottom: 15,
                          border: "1px solid #dce1eb",
                          borderRadius: 8
                        }}
                      />

                      {cameraStream && (
                        <video
                          ref={videoRef}
                          autoPlay
                          playsInline
                          muted
                          style={{
                            width: "100%",
                            maxWidth: 450,
                            display: "block",
                            borderRadius: 10,
                            marginBottom: 15
                          }}
                        />
                      )}

                      {capturedImage && (
                        <div>
                          <p className="muted">Captured face:</p>
                          <img
                            src={capturedImage}
                            alt="Captured face"
                            style={{
                              width: 220,
                              borderRadius: 10,
                              marginBottom: 15
                            }}
                          />
                        </div>
                      )}

                      <div style={{
                        display: "flex",
                        gap: 10,
                        flexWrap: "wrap"
                      }}>
                        {!cameraStream && (
                          <button type="button" onClick={startCamera}>
                            Start Camera
                          </button>
                        )}

                        {cameraStream && (
                          <button type="button" onClick={captureFace}>
                            Capture Face
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={registerPerson}
                          disabled={registrationLoading}
                        >
                          {registrationLoading
                            ? "Registering..."
                            : "Register Person"}
                        </button>

                        <button
                          type="button"
                          onClick={() => {
                            stopCamera();
                            setShowAddPerson(false);
                            setCapturedImage("");
                            setNewPersonName("");
                            setPersonError("");
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {personError && (
                <p style={{ color: "#dc2626", marginTop: 15, fontSize: 13 }}>
                  {personError}
                </p>
              )}
            </section>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

