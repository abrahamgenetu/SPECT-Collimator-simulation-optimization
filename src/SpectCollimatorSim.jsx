import React, { useState, useEffect } from 'react';
import { LineChart, Line, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Camera, Zap, Grid, TrendingUp } from 'lucide-react';

const SpectCollimatorSim = () => {
  const [simParams, setSimParams] = useState({
    holeDiameter: 1.5,
    holeLength: 25,
    septalThickness: 0.2,
    material: 'lead',
    numPhotons: 5000
  });
  
  const [results, setResults] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);

  // Material properties (attenuation coefficients for 140 keV gamma rays)
  const materials = {
    lead: { density: 11.34, attenuation: 2.3, name: 'Lead' },
    tungsten: { density: 19.25, attenuation: 1.8, name: 'Tungsten' },
    brass: { density: 8.5, attenuation: 0.8, name: 'Brass' }
  };

  // Monte Carlo simulation of photon transport
  const simulatePhotonTransport = (params) => {
    const { holeDiameter, holeLength, septalThickness, material, numPhotons } = params;
    const mat = materials[material];
    
    let detectedPhotons = [];
    let penetratedSepta = 0;
    let geometricAccepted = 0;
    
    // Simulate photons from a point source
    for (let i = 0; i < numPhotons; i++) {
      // Random emission angle (within acceptance cone)
      const theta = (Math.random() - 0.5) * Math.PI / 6; // ±30 degrees
      const phi = Math.random() * 2 * Math.PI;
      
      // Initial position at collimator face
      const x0 = (Math.random() - 0.5) * 50; // 50mm detector width
      const y0 = (Math.random() - 0.5) * 50;
      
      // Calculate trajectory
      const dx = Math.sin(theta) * Math.cos(phi);
      const dy = Math.sin(theta) * Math.sin(phi);
      const dz = Math.cos(theta);
      
      // Check geometric acceptance (simplified)
      const acceptanceAngle = Math.atan(holeDiameter / (2 * holeLength));
      
      if (Math.abs(theta) < acceptanceAngle) {
        geometricAccepted++;
        
        // Calculate path through septa
        const pathLength = holeLength / Math.cos(theta);
        const septalPath = pathLength * Math.tan(Math.abs(theta)) * 2;
        
        // Attenuation probability
        const attenuationProb = Math.exp(-mat.attenuation * septalPath);
        
        if (Math.random() < attenuationProb) {
          // Photon transmitted
          const xf = x0 + dx * holeLength / dz;
          const yf = y0 + dy * holeLength / dz;
          
          detectedPhotons.push({ x: xf, y: yf, energy: 140 * (0.95 + Math.random() * 0.1) });
        } else {
          penetratedSepta++;
        }
      }
    }
    
    // Calculate metrics
    const sensitivity = detectedPhotons.length / numPhotons;
    const spatialResolution = calculateFWHM(detectedPhotons);
    const uniformity = calculateUniformity(detectedPhotons);
    const contrastToNoise = sensitivity > 0 ? Math.sqrt(detectedPhotons.length) : 0;
    
    return {
      detectedPhotons,
      metrics: {
        sensitivity: (sensitivity * 100).toFixed(2),
        spatialResolution: spatialResolution.toFixed(2),
        uniformity: uniformity.toFixed(2),
        contrastToNoise: contrastToNoise.toFixed(1),
        geometricEfficiency: ((geometricAccepted / numPhotons) * 100).toFixed(2),
        septalPenetration: ((penetratedSepta / numPhotons) * 100).toFixed(2)
      }
    };
  };

  // Calculate Full Width Half Maximum (FWHM) - spatial resolution metric
  const calculateFWHM = (photons) => {
    if (photons.length < 10) return 0;
    
    const xPositions = photons.map(p => p.x);
    const stdDev = Math.sqrt(
      xPositions.reduce((sum, x) => sum + Math.pow(x, 2), 0) / xPositions.length
    );
    
    return 2.355 * stdDev; // FWHM = 2.355 * σ
  };

  // Calculate uniformity (coefficient of variation)
  const calculateUniformity = (photons) => {
    if (photons.length < 10) return 0;
    
    const gridSize = 5;
    const bins = Array(gridSize * gridSize).fill(0);
    
    photons.forEach(p => {
      const binX = Math.floor((p.x + 25) / 50 * gridSize);
      const binY = Math.floor((p.y + 25) / 50 * gridSize);
      const idx = Math.max(0, Math.min(gridSize * gridSize - 1, binY * gridSize + binX));
      bins[idx]++;
    });
    
    const mean = bins.reduce((a, b) => a + b, 0) / bins.length;
    const variance = bins.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / bins.length;
    
    return (1 - Math.sqrt(variance) / mean) * 100; // Uniformity percentage
  };

  const runSimulation = () => {
    setIsSimulating(true);
    setTimeout(() => {
      const result = simulatePhotonTransport(simParams);
      setResults(result);
      setIsSimulating(false);
    }, 500);
  };

  useEffect(() => {
    runSimulation();
  }, []);

  // Prepare data for visualization
  const getScatterData = () => {
    if (!results) return [];
    return results.detectedPhotons.slice(0, 500).map(p => ({
      x: p.x,
      y: p.y
    }));
  };

  const getOptimizationData = () => {
    const data = [];
    for (let d = 1.0; d <= 3.0; d += 0.25) {
      const tempParams = { ...simParams, holeDiameter: d };
      const result = simulatePhotonTransport(tempParams);
      data.push({
        diameter: d.toFixed(2),
        sensitivity: parseFloat(result.metrics.sensitivity),
        resolution: parseFloat(result.metrics.spatialResolution)
      });
    }
    return data;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <Camera className="w-10 h-10" />
            SPECT Collimator Simulation & Optimization
          </h1>
          <p className="text-blue-200 text-lg">
  Monte Carlo Photon Transport Analysis — a research tool for simulating collimator and detector parameters for small-animal (rat) studies in the CLPL lab, Marquette University.
</p>

        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Control Panel */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Grid className="w-5 h-5" />
              Collimator Parameters
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-blue-200 text-sm block mb-2">
                  Hole Diameter: {simParams.holeDiameter} mm
                </label>
                <input
                  type="range"
                  min="1.0"
                  max="3.0"
                  step="0.1"
                  value={simParams.holeDiameter}
                  onChange={(e) => setSimParams({...simParams, holeDiameter: parseFloat(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-blue-200 text-sm block mb-2">
                  Hole Length: {simParams.holeLength} mm
                </label>
                <input
                  type="range"
                  min="15"
                  max="40"
                  step="1"
                  value={simParams.holeLength}
                  onChange={(e) => setSimParams({...simParams, holeLength: parseFloat(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-blue-200 text-sm block mb-2">
                  Septal Thickness: {simParams.septalThickness} mm
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="0.5"
                  step="0.05"
                  value={simParams.septalThickness}
                  onChange={(e) => setSimParams({...simParams, septalThickness: parseFloat(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="text-blue-200 text-sm block mb-2">Material</label>
                <select
                  value={simParams.material}
                  onChange={(e) => setSimParams({...simParams, material: e.target.value})}
                  className="w-full bg-slate-800 text-white p-2 rounded border border-white/20"
                >
                  {Object.entries(materials).map(([key, val]) => (
                    <option key={key} value={key}>{val.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-blue-200 text-sm block mb-2">
                  Photons: {simParams.numPhotons.toLocaleString()}
                </label>
                <input
                  type="range"
                  min="1000"
                  max="10000"
                  step="1000"
                  value={simParams.numPhotons}
                  onChange={(e) => setSimParams({...simParams, numPhotons: parseInt(e.target.value)})}
                  className="w-full"
                />
              </div>

              <button
                onClick={runSimulation}
                disabled={isSimulating}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Zap className="w-5 h-5" />
                {isSimulating ? 'Simulating...' : 'Run Simulation'}
              </button>
            </div>
          </div>

          {/* Metrics Display */}
          <div className="lg:col-span-2 space-y-6">
            {results && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {Object.entries(results.metrics).map(([key, value]) => (
                    <div key={key} className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20">
                      <div className="text-blue-200 text-sm mb-1 capitalize">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {value}
                        {key.includes('sensitivity') || key.includes('uniformity') || key.includes('efficiency') || key.includes('penetration') ? '%' : key.includes('resolution') ? 'mm' : ''}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Detector Image */}
                <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                  <h3 className="text-lg font-bold text-white mb-4">Planar Detector Image</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                      <XAxis 
                        type="number" 
                        dataKey="x" 
                        name="X Position" 
                        unit="mm"
                        domain={[-25, 25]}
                        stroke="#60a5fa"
                      />
                      <YAxis 
                        type="number" 
                        dataKey="y" 
                        name="Y Position" 
                        unit="mm"
                        domain={[-25, 25]}
                        stroke="#60a5fa"
                      />
                      <Tooltip 
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #3b82f6' }}
                      />
                      <Scatter 
                        data={getScatterData()} 
                        fill="#3b82f6" 
                        fillOpacity={0.6}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>

                {/* Optimization Curve */}
                <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                  <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Sensitivity vs Resolution Trade-off
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={getOptimizationData()} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
                      <XAxis 
                        dataKey="diameter" 
                        label={{ value: 'Hole Diameter (mm)', position: 'insideBottom', offset: -10, fill: '#60a5fa' }}
                        stroke="#60a5fa"
                      />
                      <YAxis 
                        yAxisId="left"
                        label={{ value: 'Sensitivity (%)', angle: -90, position: 'insideLeft', fill: '#60a5fa' }}
                        stroke="#60a5fa"
                      />
                      <YAxis 
                        yAxisId="right" 
                        orientation="right"
                        label={{ value: 'Resolution (mm)', angle: 90, position: 'insideRight', fill: '#a78bfa' }}
                        stroke="#a78bfa"
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #3b82f6' }}
                      />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="sensitivity" 
                        stroke="#3b82f6" 
                        strokeWidth={3}
                        name="Sensitivity (%)"
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="resolution" 
                        stroke="#a78bfa" 
                        strokeWidth={3}
                        name="Resolution (mm FWHM)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h3 className="text-lg font-bold text-white mb-3">About This Simulation</h3>
          <p className="text-blue-200 leading-relaxed">
  This Monte Carlo simulation models gamma-ray photon transport through parallel-hole collimators for **small-animal (rat) SPECT imaging** in our lab. 
  It calculates key performance metrics including spatial resolution (FWHM), sensitivity, uniformity, and septal penetration. 
  The simulation is designed to **optimize collimator geometry and detector parameters** for small rats, balancing sensitivity and resolution under low-activity imaging conditions. 
  This tool supports our lab’s research on quantitative lung imaging and tracer distribution in rodent models.
</p>

        </div>
      </div>
    </div>
  );
};

export default SpectCollimatorSim;
