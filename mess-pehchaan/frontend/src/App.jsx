import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as faceapi from 'face-api.js';

export default function App() {
  // Screens: 'home', 'register-form', 'register-capture'
  const [screen, setScreen] = useState('home');
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [loadingError, setLoadingError] = useState(null);
  
  // Consent
  const [hasConsent, setHasConsent] = useState(() => {
    return localStorage.getItem('mess_pehchaan_consent') === 'true';
  });

  // Database Logs
  const [logs, setLogs] = useState([]);

  // Form State
  const [regName, setRegName] = useState('');
  const [regNo, setRegNo] = useState('');
  const [formError, setFormError] = useState('');

  // Camera State
  const [stream, setStream] = useState(null);
  const [cameraPermission, setCameraPermission] = useState('prompt'); // prompt, granted, denied
  const videoRef = useRef(null);
  const captureVideoRef = useRef(null);

  // Scan state
  const [scanStatus, setScanStatus] = useState('idle'); // idle, detecting, recognizing, unrecognized, error
  const [unrecognizedCount, setUnrecognizedCount] = useState(0);
  const [showRegisterBtn, setShowRegisterBtn] = useState(false);

  // Greeting State (Greeting/Display Agent)
  const [isGreetingActive, setIsGreetingActive] = useState(false);
  const [greetingData, setGreetingData] = useState(null);

  // Capture Screen State
  const [countdown, setCountdown] = useState(null);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [capturedEmbedding, setCapturedEmbedding] = useState(null);
  const [captureStatus, setCaptureStatus] = useState('idle'); // idle, counting, detecting, success, failed
  const [captureError, setCaptureError] = useState('');

  // Load face-api.js models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        console.log('Loading face-api.js models...');
        const MODEL_URL = '/models';
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
        ]);
        setModelsLoaded(true);
        console.log('face-api.js models loaded successfully.');
      } catch (err) {
        console.error('Error loading face-api models:', err);
        setLoadingError('Failed to load face detection models. Please check connection or reload.');
      }
    };
    loadModels();
    fetchLogs();
  }, []);

  // Fetch recent attendance logs
  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  };

  // Launch camera for the current screen
  useEffect(() => {
    // Stop existing stream first
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }

    if (!modelsLoaded || !hasConsent) return;

    let activeVideoRef = null;
    if (screen === 'home' && !isGreetingActive) {
      activeVideoRef = videoRef;
    } else if (screen === 'register-capture') {
      activeVideoRef = captureVideoRef;
    }

    if (!activeVideoRef) return;

    const startCamera = async () => {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user'
          }
        });
        setStream(mediaStream);
        setCameraPermission('granted');
        if (activeVideoRef.current) {
          activeVideoRef.current.srcObject = mediaStream;
        }
      } catch (err) {
        console.error('Error accessing webcam:', err);
        setCameraPermission('denied');
      }
    };

    startCamera();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [screen, modelsLoaded, hasConsent, isGreetingActive]);

  // Capture Agent loop (Continuous scanning on home screen)
  useEffect(() => {
    if (screen !== 'home' || !modelsLoaded || !stream || isGreetingActive || !hasConsent) return;

    const scanInterval = setInterval(async () => {
      if (!videoRef.current || isGreetingActive) return;

      setScanStatus('detecting');
      try {
        // Run face detector
        const detection = await faceapi
          .detectSingleFace(
            videoRef.current,
            new faceapi.TinyFaceDetectorOptions({ inputSize: 160, scoreThreshold: 0.5 })
          )
          .withFaceLandmarks()
          .withFaceDescriptor();

        if (detection) {
          setScanStatus('recognizing');
          // Recognition Agent: Send to backend
          const response = await fetch('/api/recognize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ face_embedding: Array.from(detection.descriptor) })
          });

          if (!response.ok) {
            throw new Error('Server recognition call failed');
          }

          const data = await response.json();

          if (data.match) {
            // Match found -> trigger Greeting Overlay (Greeting/Display Agent)
            setGreetingData(data);
            setIsGreetingActive(true);
            setUnrecognizedCount(0);
            setShowRegisterBtn(false);

            // Display for exactly 3 seconds
            setTimeout(() => {
              setIsGreetingActive(false);
              setGreetingData(null);
              fetchLogs(); // refresh logs
            }, 3000);
          } else {
            // Unrecognized face detected
            setScanStatus('unrecognized');
            setUnrecognizedCount(prev => {
              const newCount = prev + 1;
              // If unrecognized 2 consecutive times, show register button
              if (newCount >= 2) {
                setShowRegisterBtn(true);
              }
              return newCount;
            });
          }
        } else {
          // No face in frame
          setScanStatus('idle');
        }
      } catch (err) {
        console.error('Scanning error:', err);
        setScanStatus('error');
      }
    }, 2500);

    return () => clearInterval(scanInterval);
  }, [screen, modelsLoaded, stream, isGreetingActive, hasConsent]);

  // Handle privacy consent
  const handleGrantConsent = () => {
    localStorage.setItem('mess_pehchaan_consent', 'true');
    setHasConsent(true);
  };

  // Form Next click
  const handleFormNext = (e) => {
    e.preventDefault();
    if (!regName.trim()) {
      setFormError('Please enter name');
      return;
    }
    if (!regNo.trim()) {
      setFormError('Please enter registration number');
      return;
    }
    // Simple VIT Reg No check: e.g. 21BDS0112 (9-digit alphanumeric)
    const cleanReg = regNo.trim().toUpperCase();
    if (cleanReg.length < 8 || cleanReg.length > 12) {
      setFormError('Please enter a valid VIT registration number (e.g. 21BCE0001)');
      return;
    }
    setRegNo(cleanReg);
    setFormError('');
    setCapturedPhoto(null);
    setCapturedEmbedding(null);
    setCaptureStatus('idle');
    setScreen('register-capture');
  };

  // Face Registration capture countdown & extraction
  const startRegistrationCapture = () => {
    if (captureStatus === 'counting' || captureStatus === 'detecting') return;
    setCaptureStatus('counting');
    setCountdown(3);
  };

  // Countdown timer effect
  useEffect(() => {
    if (countdown === null) return;

    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setCountdown(null);
      captureSnapshot();
    }
  }, [countdown]);

  // Capture frame and extract embedding
  const captureSnapshot = async () => {
    if (!captureVideoRef.current) {
      setCaptureStatus('failed');
      setCaptureError('Webcam not active.');
      return;
    }

    setCaptureStatus('detecting');
    setCaptureError('');

    try {
      const video = captureVideoRef.current;
      
      // Extract face descriptor
      const detection = await faceapi
        .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
        .withFaceLandmarks()
        .withFaceDescriptor();

      if (!detection) {
        setCaptureStatus('failed');
        setCaptureError('No face detected. Please position your face clearly in the center and retry.');
        return;
      }

      // Draw snapshot to canvas to create visual preview
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      // Mirror the context so image matches mirrored camera stream
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg');

      setCapturedPhoto(dataUrl);
      setCapturedEmbedding(Array.from(detection.descriptor));
      setCaptureStatus('success');
    } catch (err) {
      console.error('Error during capture:', err);
      setCaptureStatus('failed');
      setCaptureError('Error processing facial details. Try again.');
    }
  };

  // Submit registration to backend
  const handleConfirmRegistration = async () => {
    if (!capturedEmbedding) return;

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: regName,
          reg_no: regNo,
          face_embedding: capturedEmbedding
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Reset states and return home
        setRegName('');
        setRegNo('');
        setCapturedPhoto(null);
        setCapturedEmbedding(null);
        setScreen('home');
        setUnrecognizedCount(0);
        setShowRegisterBtn(false);
        fetchLogs();
      } else {
        setCaptureError(data.error || 'Failed to complete registration.');
      }
    } catch (err) {
      console.error('Registration failed:', err);
      setCaptureError('Network error registering face. Try again.');
    }
  };

  // Simulation: Scan a test image
  const simulateScan = async (imageUrl) => {
    setScanStatus('detecting');
    try {
      const img = new Image();
      img.src = imageUrl;
      img.onload = async () => {
        // Draw to temporary canvas
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);

        try {
          // Detect face on image
          const detection = await faceapi
            .detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
            .withFaceLandmarks()
            .withFaceDescriptor();

          if (detection) {
            setScanStatus('recognizing');
            // Send embedding to recognition endpoint
            const response = await fetch('/api/recognize', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ face_embedding: Array.from(detection.descriptor) })
            });
            const data = await response.json();

            if (data.match) {
              setGreetingData(data);
              setIsGreetingActive(true);
              setUnrecognizedCount(0);
              setShowRegisterBtn(false);
              setTimeout(() => {
                setIsGreetingActive(false);
                setGreetingData(null);
                fetchLogs();
              }, 3000);
            } else {
              setScanStatus('unrecognized');
              setUnrecognizedCount(prev => {
                const newCount = prev + 1;
                if (newCount >= 2) {
                  setShowRegisterBtn(true);
                }
                return newCount;
              });
            }
          } else {
            setScanStatus('idle');
            alert('No face detected in the test image! Ensure it is loaded correctly.');
          }
        } catch (err) {
          console.error('Simulation scan error:', err);
          setScanStatus('error');
        }
      };
    } catch (err) {
      console.error('Failed to load image:', err);
      setScanStatus('error');
    }
  };

  // Simulation: Capture a test image during registration
  const simulateCapture = async (imageUrl) => {
    setCaptureStatus('detecting');
    setCaptureError('');
    try {
      const img = new Image();
      img.src = imageUrl;
      img.onload = async () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);

        try {
          const detection = await faceapi
            .detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 }))
            .withFaceLandmarks()
            .withFaceDescriptor();

          if (!detection) {
            setCaptureStatus('failed');
            setCaptureError('No face detected in the test image.');
            return;
          }

          setCapturedPhoto(imageUrl);
          setCapturedEmbedding(Array.from(detection.descriptor));
          setCaptureStatus('success');
        } catch (err) {
          console.error('Simulation capture error:', err);
          setCaptureStatus('failed');
          setCaptureError('Failed to extract face embedding from test image.');
        }
      };
    } catch (err) {
      console.error('Failed to load image for registration:', err);
      setCaptureStatus('failed');
      setCaptureError('Failed to load test image.');
    }
  };

  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-between pb-8">
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-950/40 via-slate-950 to-slate-950 -z-10" />

      {/* Header */}
      <header className="w-full max-w-5xl px-6 py-4 flex flex-col md:flex-row items-center justify-between border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-amber-400 to-amber-500 rounded-lg flex items-center justify-center font-bold text-slate-950 shadow-lg shadow-amber-500/20">
            VP
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-slate-100 via-amber-400 to-amber-500 bg-clip-text text-transparent">
              VIT CHENNAI NON-VEG MESS
            </h1>
            <p className="text-xs text-slate-400">Mess Attendance & Facial Attendance Register</p>
          </div>
        </div>
        <div className="mt-3 md:mt-0 flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-emerald-400">System Online</span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="w-full max-w-5xl px-4 flex-grow flex flex-col items-center justify-center py-6">
        <AnimatePresence mode="wait">
          {/* 1. Loading models state */}
          {!modelsLoaded && !loadingError && (
            <motion.div
              key="loading-models"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center space-y-4 py-20"
            >
              <div className="w-12 h-12 border-4 border-amber-400 border-t-transparent rounded-full animate-spin" />
              <p className="text-slate-400 font-medium animate-pulse text-sm">Loading Neural Networks & Face Models...</p>
            </motion.div>
          )}

          {/* 2. Loading error state */}
          {loadingError && (
            <motion.div
              key="loading-error"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="max-w-md w-full p-6 rounded-2xl bg-red-950/20 border border-red-900/50 text-center"
            >
              <div className="text-red-400 text-3xl mb-3">⚠️</div>
              <h3 className="font-semibold text-lg text-red-200">System Error</h3>
              <p className="text-sm text-red-300/80 mt-1">{loadingError}</p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 px-4 py-2 bg-red-900/40 hover:bg-red-900/60 text-red-200 text-sm font-medium rounded-lg border border-red-800 transition"
              >
                Reload Application
              </button>
            </motion.div>
          )}

          {/* 3. Consent Overlay */}
          {modelsLoaded && !hasConsent && (
            <motion.div
              key="consent"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="max-w-lg w-full p-8 rounded-3xl bg-slate-900/90 border border-slate-800 backdrop-blur-xl shadow-2xl flex flex-col items-center text-center space-y-6"
            >
              <div className="w-16 h-16 bg-amber-400/10 border border-amber-400/20 text-amber-400 rounded-full flex items-center justify-center text-2xl font-bold">
                🔑
              </div>
              <h2 className="text-2xl font-bold text-slate-100">Biometric Scan Consent</h2>
              <div className="text-sm text-slate-300 space-y-3 leading-relaxed text-left">
                <p>
                  To mark attendance in the VIT Chennai Non-Veg Mess, this application uses the camera to scan and identify your face.
                </p>
                <p className="font-semibold text-amber-300/90">
                  🔒 Privacy Information:
                </p>
                <ul className="list-disc pl-5 space-y-1 text-slate-400">
                  <li>Your face video stream is processed <strong>locally in the browser</strong>.</li>
                  <li>No raw photos or video feeds are sent to the server.</li>
                  <li>Only a 128-number face descriptor is transmitted to verify your identity.</li>
                </ul>
              </div>
              <button
                onClick={handleGrantConsent}
                className="w-full py-3 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-slate-950 font-semibold rounded-xl transition duration-200 shadow-lg shadow-amber-500/20"
              >
                Accept and Open Camera
              </button>
            </motion.div>
          )}

          {/* 4. HOME SCREEN (Capture & Attendance Loop) */}
          {modelsLoaded && hasConsent && screen === 'home' && !isGreetingActive && (
            <motion.div
              key="home-screen"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-start"
            >
              {/* Left Column: Camera Preview */}
              <div className="lg:col-span-7 flex flex-col items-center">
                <div className="relative w-full max-w-md aspect-[4/3] rounded-3xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl">
                  {cameraPermission === 'denied' ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-slate-900">
                      <p className="text-amber-500 text-4xl mb-2">📷</p>
                      <h4 className="font-semibold text-slate-200">Webcam Not Available</h4>
                      <p className="text-xs text-slate-400 mt-1 max-w-xs">
                        Webcam permission was denied or not found. You can still test the system using the preloaded test images below!
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Video Stream */}
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover scale-x-[-1]"
                      />
                      
                      {/* Scanning HUD Overlays */}
                      <div className="absolute inset-0 border-[3px] border-dashed border-slate-500/10 pointer-events-none rounded-3xl" />
                      
                      {/* Scanning Guideline silhouette */}
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="w-56 h-72 border-2 border-dashed border-slate-500/30 rounded-[110px] relative">
                          <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-950/80 px-3 py-1 rounded-full border border-slate-800/80 text-[10px] font-semibold text-slate-400 tracking-wider">
                            ALIGN FACE
                          </div>
                        </div>
                      </div>

                      {/* Moving laser scan effect */}
                      <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-amber-400 to-transparent opacity-40 top-0 animate-[scan_3s_linear_infinite]" />

                      {/* Scan Status Floating Tag */}
                      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between px-4 py-2 rounded-2xl bg-slate-950/80 border border-slate-800/80 backdrop-blur-md">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            scanStatus === 'detecting' ? 'bg-amber-400 animate-pulse' :
                            scanStatus === 'recognizing' ? 'bg-indigo-400 animate-ping' :
                            scanStatus === 'unrecognized' ? 'bg-red-500' : 'bg-slate-500'
                          }`} />
                          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                            {scanStatus === 'idle' && 'Waiting for face...'}
                            {scanStatus === 'detecting' && 'Detecting...'}
                            {scanStatus === 'recognizing' && 'Checking database...'}
                            {scanStatus === 'unrecognized' && 'Not recognized'}
                            {scanStatus === 'error' && 'Scanner Error'}
                          </span>
                        </div>
                        {scanStatus === 'detecting' && (
                          <div className="text-[10px] text-amber-400">Processing Biometrics</div>
                        )}
                      </div>
                    </>
                  )}
                </div>

                {/* Floating Register Button if not recognized */}
                <AnimatePresence>
                  {showRegisterBtn && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 15 }}
                      className="mt-4 w-full max-w-md"
                    >
                      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl text-center space-y-3">
                        <p className="text-xs text-slate-400">Face not matching any registered mess record?</p>
                        <button
                          onClick={() => setScreen('register-form')}
                          className="w-full py-2.5 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-amber-500/10"
                        >
                          Register Face Embeddings
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Right Column: Recent Activity Feed */}
              <div className="lg:col-span-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold tracking-tight text-slate-200">Recent Attendance Logs</h3>
                  <button 
                    onClick={fetchLogs} 
                    className="p-1.5 hover:bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-400 hover:text-slate-200 transition"
                  >
                    🔄 Refresh
                  </button>
                </div>
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden max-h-[350px] overflow-y-auto">
                  {logs.length === 0 ? (
                    <div className="p-8 text-center text-slate-500 text-xs">
                      No attendance scans recorded today.
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-800">
                      {logs.map((log) => (
                        <div key={log.id} className="p-3 flex items-center justify-between text-xs hover:bg-slate-900/50 transition">
                          <div>
                            <div className="font-semibold text-slate-200">{log.name}</div>
                            <div className="text-[10px] text-slate-400">{log.reg_no}</div>
                          </div>
                          <div className="text-right">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                              log.meal_type === 'Breakfast' ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20' :
                              log.meal_type === 'Lunch' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                              log.meal_type === 'Snacks' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                              'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                            }`}>
                              {log.meal_type}
                            </span>
                            <div className="text-[9px] text-slate-500 mt-1">
                              {new Date(log.marked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {/* Fallback persistent manual Register Trigger */}
                <div className="text-center">
                  <button
                    onClick={() => setScreen('register-form')}
                    className="text-xs text-slate-500 hover:text-amber-400 underline font-medium transition"
                  >
                    Manual New Student Registration
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* 5. GREETING OVERLAY (Greeting/Display Agent) */}
          {isGreetingActive && greetingData && (
            <motion.div
              key="greeting-overlay"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl text-center space-y-6 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl -z-10" />

              <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-3xl mx-auto shadow-lg shadow-emerald-500/5">
                ✓
              </div>

              <div>
                <h2 className="text-2xl font-bold text-slate-100">{greetingData.name}</h2>
                <p className="text-sm font-semibold text-slate-400 mt-0.5 uppercase tracking-wider">{greetingData.reg_no}</p>
              </div>

              <div className="py-4 px-6 bg-slate-950/60 rounded-2xl border border-slate-800/60">
                <p className="text-sm leading-relaxed text-amber-300/90 font-medium">
                  {greetingData.greeting}
                </p>
              </div>

              {greetingData.rate_limited ? (
                <p className="text-[10px] text-slate-500">
                  Attendance already locked in. (Rate-limited for 30s)
                </p>
              ) : (
                <div className="flex items-center justify-center gap-1.5 text-xs text-emerald-400 font-semibold bg-emerald-500/5 py-1 px-3 rounded-full border border-emerald-500/10 w-fit mx-auto">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
                  Attendance Checked In
                </div>
              )}
            </motion.div>
          )}

          {/* 6. REGISTRATION DETAILS FORM */}
          {screen === 'register-form' && (
            <motion.div
              key="register-form"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-6"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-xl font-bold">Register Student</h2>
                  <p className="text-xs text-slate-400">Step 1 of 2: Fill Details</p>
                </div>
                <button
                  onClick={() => setScreen('home')}
                  className="text-xs px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition"
                >
                  Cancel
                </button>
              </div>

              <form onSubmit={handleFormNext} className="space-y-4">
                {formError && (
                  <div className="p-3 bg-red-950/20 border border-red-900/50 rounded-xl text-xs text-red-300">
                    ⚠️ {formError}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label htmlFor="reg-name" className="text-xs font-semibold text-slate-300">
                    Full Name
                  </label>
                  <input
                    id="reg-name"
                    type="text"
                    required
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder="Enter student name"
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-amber-400 focus:outline-none transition"
                  />
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="reg-no" className="text-xs font-semibold text-slate-300">
                    VIT Registration Number
                  </label>
                  <input
                    id="reg-no"
                    type="text"
                    required
                    value={regNo}
                    onChange={(e) => setRegNo(e.target.value)}
                    placeholder="e.g. 21BCE0001"
                    className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:border-amber-400 focus:outline-none transition uppercase"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-amber-500/10"
                >
                  Next: Setup Face Scan
                </button>
              </form>
            </motion.div>
          )}

          {/* 7. REGISTRATION FACE CAPTURE SCREEN */}
          {screen === 'register-capture' && (
            <motion.div
              key="register-capture"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="max-w-md w-full p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-6"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-xl font-bold">Register Face</h2>
                  <p className="text-xs text-slate-400">Step 2 of 2: Scan Embedding</p>
                </div>
                <button
                  onClick={() => setScreen('register-form')}
                  className="text-xs px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition"
                  disabled={captureStatus === 'counting' || captureStatus === 'detecting'}
                >
                  Back
                </button>
              </div>

              {/* Scanner Screen Frame */}
              <div className="relative w-full aspect-[4/3] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden flex items-center justify-center">
                {!capturedPhoto ? (
                  <>
                    <video
                      ref={captureVideoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover scale-x-[-1]"
                    />
                    
                    {/* Face Overlay Guideline */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-48 h-60 border-2 border-dashed border-amber-400/40 rounded-[90px] relative">
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-950/80 px-2 py-0.5 rounded-full border border-slate-800/80 text-[9px] font-semibold text-amber-400">
                          CENTER FACE
                        </div>
                      </div>
                    </div>

                    {/* Countdown Overlay */}
                    {countdown !== null && (
                      <div className="absolute inset-0 bg-slate-950/70 flex items-center justify-center">
                        <motion.span
                          key={countdown}
                          initial={{ opacity: 0, scale: 0.5 }}
                          animate={{ opacity: 1, scale: 1.8 }}
                          exit={{ opacity: 0, scale: 2.2 }}
                          transition={{ duration: 0.8 }}
                          className="text-5xl font-black text-amber-400"
                        >
                          {countdown === 0 ? 'Capture!' : countdown}
                        </motion.span>
                      </div>
                    )}

                    {/* Detecting Neural Net Spinner */}
                    {captureStatus === 'detecting' && (
                      <div className="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center space-y-3">
                        <div className="w-8 h-8 border-4 border-amber-400 border-t-transparent rounded-full animate-spin" />
                        <p className="text-xs text-amber-400">Computing 128-D Vector Embeddings...</p>
                      </div>
                    )}
                  </>
                ) : (
                  <img
                    src={capturedPhoto}
                    alt="Captured preview"
                    className="w-full h-full object-cover"
                  />
                )}
              </div>

              {/* Status and Actions */}
              <div className="space-y-4">
                {captureError && (
                  <div className="p-3 bg-red-950/20 border border-red-900/50 rounded-xl text-xs text-red-300 text-center">
                    {captureError}
                  </div>
                )}

                {captureStatus === 'success' && (
                  <div className="p-3 bg-emerald-950/20 border border-emerald-900/50 rounded-xl text-xs text-emerald-300 text-center font-medium">
                    ✓ Face scanned successfully and vector computed!
                  </div>
                )}

                <div className="flex gap-4">
                  {!capturedPhoto ? (
                    <button
                      onClick={startRegistrationCapture}
                      disabled={captureStatus === 'counting' || captureStatus === 'detecting'}
                      className="w-full py-3 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-amber-500/10"
                    >
                      {captureStatus === 'counting' ? 'Preparing camera...' : 'Scan Face via Webcam'}
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setCapturedPhoto(null);
                          setCapturedEmbedding(null);
                          setCaptureStatus('idle');
                        }}
                        className="w-1/2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl text-sm transition border border-slate-700"
                      >
                        Retake
                      </button>
                      <button
                        onClick={handleConfirmRegistration}
                        className="w-1/2 py-2.5 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-amber-500/10"
                      >
                        Confirm & Save
                      </button>
                    </>
                  )}
                </div>


              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="text-center text-[10px] text-slate-500 max-w-md px-6">
        Mess Pehchaan Attendance System © 2026. Designed for VIT Chennai Campus, Vandalur-Kelambakkam Road. Local processing keeps biometric data secure.
      </footer>
    </div>
  );
}
