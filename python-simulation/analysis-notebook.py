"""
SPECT Collimator Analysis Notebook
Interactive exploration and visualization of simulation results

Save this as analysis_notebook.ipynb and run with Jupyter
"""

# Cell 1: Setup and Imports
print("Setting up environment...")

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from spect_simulation import SPECTSimulator, CollimatorParams, MATERIALS
import seaborn as sns

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("✓ Imports successful")

# Cell 2: Quick Simulation
print("Running quick simulation...")

params = CollimatorParams(
    hole_diameter=1.5,
    hole_length=25.0,
    septal_thickness=0.2,
    material='lead'
)

simulator = SPECTSimulator(params)
results = simulator.simulate_photon_transport(num_photons=5000)
metrics = simulator.calculate_metrics(results)

print(f"\nQuick Results:")
print(f"  Detected: {results['detected_count']:,} / {results['total_photons']:,} photons")
print(f"  Sensitivity: {metrics['sensitivity']:.3f}%")
print(f"  Resolution: {metrics['spatial_resolution_fwhm']:.2f} mm FWHM")

# Cell 3: Visualize Detector Image
print("Creating detector image visualization...")

photons = results['detected_photons']
x = np.array([p['x'] for p in photons])
y = np.array([p['y'] for p in photons])

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# 2D Histogram
h = axes[0].hist2d(x, y, bins=40, cmap='hot')
axes[0].set_title('Planar Detector Image', fontsize=14, fontweight='bold')
axes[0].set_xlabel('X Position (mm)')
axes[0].set_ylabel('Y Position (mm)')
axes[0].set_aspect('equal')
plt.colorbar(h[3], ax=axes[0], label='Counts')

# X Profile
axes[1].hist(x, bins=50, color='blue', alpha=0.7, edgecolor='black')
axes[1].set_title('X-axis Profile', fontsize=14, fontweight='bold')
axes[1].set_xlabel('X Position (mm)')
axes[1].set_ylabel('Counts')
axes[1].axvline(0, color='red', linestyle='--', linewidth=2, label='Center')
axes[1].legend()

# Y Profile
axes[2].hist(y, bins=50, color='green', alpha=0.7, edgecolor='black')
axes[2].set_title('Y-axis Profile', fontsize=14, fontweight='bold')
axes[2].set_xlabel('Y Position (mm)')
axes[2].set_ylabel('Counts')
axes[2].axvline(0, color='red', linestyle='--', linewidth=2, label='Center')
axes[2].legend()

plt.tight_layout()
plt.show()

# Cell 4: Energy Spectrum Analysis
print("Analyzing energy spectrum...")

energies = np.array([p['energy'] for p in photons])

fig, ax = plt.subplots(figsize=(10, 6))
counts, bins, _ = ax.hist(energies, bins=60, color='purple', alpha=0.7, edgecolor='black')
ax.set_title('Energy Spectrum (Tc-99m: 140 keV)', fontsize=16, fontweight='bold')
ax.set_xlabel('Energy (keV)', fontsize=12)
ax.set_ylabel('Counts', fontsize=12)
ax.axvline(140, color='red', linestyle='--', linewidth=2, label='140 keV Photopeak')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11)

# Calculate energy resolution
peak_energy = 140
energy_window = energies[(energies > 130) & (energies < 150)]
fwhm = 2.355 * np.std(energy_window)
resolution_percent = (fwhm / peak_energy) * 100

ax.text(0.98, 0.97, f'Energy Resolution: {resolution_percent:.1f}% FWHM', 
        transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.show()

print(f"\nEnergy Resolution: {resolution_percent:.2f}% FWHM at 140 keV")

# Cell 5: Parameter Sensitivity Study
print("Running parameter sensitivity study...")
print("This may take a minute...")

diameters = np.linspace(1.0, 2.5, 8)
results_sensitivity = []

for d in diameters:
    params_temp = CollimatorParams(
        hole_diameter=d,
        hole_length=25.0,
        septal_thickness=0.2,
        material='lead'
    )
    
    sim = SPECTSimulator(params_temp)
    res = sim.simulate_photon_transport(num_photons=2000)
    met = sim.calculate_metrics(res)
    
    results_sensitivity.append({
        'diameter': d,
        'sensitivity': met['sensitivity'],
        'resolution': met['spatial_resolution_fwhm']
    })
    print(f"  Diameter {d:.2f}mm: Sensitivity={met['sensitivity']:.3f}%, Resolution={met['spatial_resolution_fwhm']:.2f}mm")

df_sensitivity = pd.DataFrame(results_sensitivity)

# Cell 6: Plot Sensitivity Analysis
print("Creating sensitivity analysis plots...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Sensitivity vs Diameter
axes[0].plot(df_sensitivity['diameter'], df_sensitivity['sensitivity'], 
            'o-', linewidth=2, markersize=8, color='blue')
axes[0].set_xlabel('Hole Diameter (mm)', fontsize=12)
axes[0].set_ylabel('Sensitivity (%)', fontsize=12)
axes[0].set_title('Sensitivity vs Hole Diameter', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3)

# Resolution vs Diameter
axes[1].plot(df_sensitivity['diameter'], df_sensitivity['resolution'], 
            'o-', linewidth=2, markersize=8, color='red')
axes[1].set_xlabel('Hole Diameter (mm)', fontsize=12)
axes[1].set_ylabel('Spatial Resolution (mm FWHM)', fontsize=12)
axes[1].set_title('Resolution vs Hole Diameter', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Cell 7: Trade-off Curve
print("Creating sensitivity-resolution trade-off curve...")

fig, ax = plt.subplots(figsize=(10, 7))

sc = ax.scatter(df_sensitivity['sensitivity'], 
               df_sensitivity['resolution'],
               c=df_sensitivity['diameter'],
               s=200,
               cmap='viridis',
               edgecolors='black',
               linewidths=2)

# Add labels for each point
for _, row in df_sensitivity.iterrows():
    ax.annotate(f"{row['diameter']:.1f}mm", 
               (row['sensitivity'], row['resolution']),
               xytext=(5, 5), textcoords='offset points',
               fontsize=9, fontweight='bold')

ax.set_xlabel('Sensitivity (%)', fontsize=13)
ax.set_ylabel('Spatial Resolution (mm FWHM)', fontsize=13)
ax.set_title('Sensitivity vs Resolution Trade-off\n(Color indicates hole diameter)', 
            fontsize=15, fontweight='bold')
ax.grid(True, alpha=0.3)

cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('Hole Diameter (mm)', fontsize=11)

plt.tight_layout()
plt.show()

print("\n✓ Analysis complete!")

# Cell 8: Material Comparison
print("Comparing collimator materials...")

materials_to_test = ['lead', 'tungsten', 'brass']
material_results = []

for mat in materials_to_test:
    params_mat = CollimatorParams(
        hole_diameter=1.5,
        hole_length=25.0,
        septal_thickness=0.2,
        material=mat
    )
    
    sim = SPECTSimulator(params_mat)
    res = sim.simulate_photon_transport(num_photons=3000)
    met = sim.calculate_metrics(res)
    
    material_results.append({
        'Material': MATERIALS[mat].name,
        'Sensitivity': met['sensitivity'],
        'Resolution': met['spatial_resolution_fwhm'],
        'Septal Penetration': met['septal_penetration_fraction']
    })
    
    print(f"  {MATERIALS[mat].name}: Sensitivity={met['sensitivity']:.3f}%, "
          f"Septal Penetration={met['septal_penetration_fraction']:.2f}%")

df_materials = pd.DataFrame(material_results)

# Plot material comparison
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

df_materials.plot(x='Material', y='Sensitivity', kind='bar', ax=axes[0], color='steelblue', legend=False)
axes[0].set_title('Sensitivity by Material', fontweight='bold')
axes[0].set_ylabel('Sensitivity (%)')
axes[0].set_xlabel('')

df_materials.plot(x='Material', y='Resolution', kind='bar', ax=axes[1], color='coral', legend=False)
axes[1].set_title('Spatial Resolution by Material', fontweight='bold')
axes[1].set_ylabel('Resolution (mm FWHM)')
axes[1].set_xlabel('')

df_materials.plot(x='Material', y='Septal Penetration', kind='bar', ax=axes[2], color='lightgreen', legend=False)
axes[2].set_title('Septal Penetration by Material', fontweight='bold')
axes[2].set_ylabel('Penetration (%)')
axes[2].set_xlabel('')

plt.tight_layout()
plt.show()

# Cell 9: Summary Statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nMaterial Comparison:")
print(df_materials.to_string(index=False))

print("\n\nParameter Sensitivity:")
print(f"  Diameter Range: {df_sensitivity['diameter'].min():.1f} - {df_sensitivity['diameter'].max():.1f} mm")
print(f"  Sensitivity Range: {df_sensitivity['sensitivity'].min():.3f} - {df_sensitivity['sensitivity'].max():.3f}%")
print(f"  Resolution Range: {df_sensitivity['resolution'].min():.2f} - {df_sensitivity['resolution'].max():.2f} mm")

sensitivity_change = ((df_sensitivity['sensitivity'].max() - df_sensitivity['sensitivity'].min()) / 
                     df_sensitivity['sensitivity'].min() * 100)
resolution_change = ((df_sensitivity['resolution'].max() - df_sensitivity['resolution'].min()) / 
                    df_sensitivity['resolution'].min() * 100)

print(f"\n  Sensitivity change across diameter range: {sensitivity_change:.1f}%")
print(f"  Resolution change across diameter range: {resolution_change:.1f}%")

print("\n" + "="*60)

# Cell 10: Export Results
print("\nExporting results to CSV...")

df_sensitivity.to_csv('sensitivity_study.csv', index=False)
df_materials.to_csv('material_comparison.csv', index=False)

print("✓ Results exported:")
print("  - sensitivity_study.csv")
print("  - material_comparison.csv")

print("\n🎉 Notebook analysis complete!")
print("\nNext steps:")
print("  1. Try modifying parameters in earlier cells")
print("  2. Run more detailed optimization with optimize_collimator.py")
print("  3. Explore different collimator geometries")
print("  4. Compare with experimental data if available")