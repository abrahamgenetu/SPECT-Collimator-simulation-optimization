"""
SPECT Collimator Parameter Optimization
Performs systematic parameter sweep to find optimal design trade-offs

This script explores the sensitivity vs resolution trade-off space
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from spect_simulation import SPECTSimulator, CollimatorParams, MATERIALS

def parameter_sweep_analysis():
    """
    Comprehensive parameter sweep to analyze design trade-offs
    """
    print("Starting Comprehensive Parameter Sweep...")
    print("="*60)
    
    # Define parameter ranges
    hole_diameters = np.linspace(1.0, 3.0, 9)  # mm
    hole_lengths = np.linspace(20, 35, 7)      # mm
    materials = ['lead', 'tungsten']
    
    results = []
    total_simulations = len(hole_diameters) * len(hole_lengths) * len(materials)
    current = 0
    
    for material in materials:
        for diameter in hole_diameters:
            for length in hole_lengths:
                current += 1
                print(f"\rProgress: {current}/{total_simulations} "
                      f"({100*current/total_simulations:.1f}%)", end='')
                
                params = CollimatorParams(
                    hole_diameter=diameter,
                    hole_length=length,
                    septal_thickness=0.2,
                    material=material
                )
                
                simulator = SPECTSimulator(params)
                sim_results = simulator.simulate_photon_transport(num_photons=3000)
                metrics = simulator.calculate_metrics(sim_results)
                
                results.append({
                    'material': material,
                    'hole_diameter': diameter,
                    'hole_length': length,
                    'sensitivity': metrics['sensitivity'],
                    'resolution': metrics['spatial_resolution_fwhm'],
                    'uniformity': metrics['uniformity'],
                    'septal_penetration': metrics['septal_penetration_fraction'],
                    'figure_of_merit': metrics['sensitivity'] * metrics['uniformity'] / metrics['spatial_resolution_fwhm']
                })
    
    print("\n\nParameter sweep complete!")
    return pd.DataFrame(results)

def visualize_optimization_results(df):
    """
    Create comprehensive visualization of optimization results
    """
    fig = plt.figure(figsize=(18, 12))
    
    # 1. Sensitivity vs Resolution Trade-off (3D for hole length)
    ax1 = fig.add_subplot(2, 3, 1, projection='3d')
    lead_data = df[df['material'] == 'lead']
    
    scatter = ax1.scatter(lead_data['sensitivity'], 
                         lead_data['resolution'],
                         lead_data['hole_length'],
                         c=lead_data['hole_diameter'],
                         cmap='viridis',
                         s=100,
                         alpha=0.6)
    
    ax1.set_xlabel('Sensitivity (%)', fontsize=10)
    ax1.set_ylabel('Resolution (mm)', fontsize=10)
    ax1.set_zlabel('Hole Length (mm)', fontsize=10)
    ax1.set_title('3D Trade-off Space (Lead)', fontweight='bold')
    plt.colorbar(scatter, ax=ax1, label='Hole Diameter (mm)')
    
    # 2. Sensitivity vs Resolution by Material
    ax2 = fig.add_subplot(2, 3, 2)
    for material in df['material'].unique():
        material_data = df[df['material'] == material]
        ax2.scatter(material_data['sensitivity'], 
                   material_data['resolution'],
                   label=material.capitalize(),
                   alpha=0.6,
                   s=50)
    
    ax2.set_xlabel('Sensitivity (%)', fontsize=11)
    ax2.set_ylabel('Spatial Resolution (mm FWHM)', fontsize=11)
    ax2.set_title('Sensitivity vs Resolution by Material', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Heatmap: Sensitivity vs Diameter and Length (Lead)
    ax3 = fig.add_subplot(2, 3, 3)
    pivot_sensitivity = lead_data.pivot_table(
        values='sensitivity',
        index='hole_length',
        columns='hole_diameter',
        aggfunc='mean'
    )
    
    im = ax3.imshow(pivot_sensitivity, aspect='auto', cmap='YlOrRd', origin='lower')
    ax3.set_xticks(range(len(pivot_sensitivity.columns)))
    ax3.set_xticklabels([f'{x:.1f}' for x in pivot_sensitivity.columns], rotation=45)
    ax3.set_yticks(range(len(pivot_sensitivity.index)))
    ax3.set_yticklabels([f'{x:.0f}' for x in pivot_sensitivity.index])
    ax3.set_xlabel('Hole Diameter (mm)', fontsize=11)
    ax3.set_ylabel('Hole Length (mm)', fontsize=11)
    ax3.set_title('Sensitivity Heatmap (%)', fontweight='bold')
    plt.colorbar(im, ax=ax3)
    
    # 4. Heatmap: Resolution vs Diameter and Length (Lead)
    ax4 = fig.add_subplot(2, 3, 4)
    pivot_resolution = lead_data.pivot_table(
        values='resolution',
        index='hole_length',
        columns='hole_diameter',
        aggfunc='mean'
    )
    
    im = ax4.imshow(pivot_resolution, aspect='auto', cmap='viridis', origin='lower')
    ax4.set_xticks(range(len(pivot_resolution.columns)))
    ax4.set_xticklabels([f'{x:.1f}' for x in pivot_resolution.columns], rotation=45)
    ax4.set_yticks(range(len(pivot_resolution.index)))
    ax4.set_yticklabels([f'{x:.0f}' for x in pivot_resolution.index])
    ax4.set_xlabel('Hole Diameter (mm)', fontsize=11)
    ax4.set_ylabel('Hole Length (mm)', fontsize=11)
    ax4.set_title('Spatial Resolution Heatmap (mm)', fontweight='bold')
    plt.colorbar(im, ax=ax4)
    
    # 5. Figure of Merit Analysis
    ax5 = fig.add_subplot(2, 3, 5)
    for material in df['material'].unique():
        material_data = df[df['material'] == material]
        ax5.scatter(material_data['hole_diameter'],
                   material_data['figure_of_merit'],
                   label=material.capitalize(),
                   alpha=0.6)
    
    ax5.set_xlabel('Hole Diameter (mm)', fontsize=11)
    ax5.set_ylabel('Figure of Merit (Sensitivity×Uniformity/Resolution)', fontsize=11)
    ax5.set_title('Overall Performance Metric', fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Pareto Front
    ax6 = fig.add_subplot(2, 3, 6)
    
    # Find Pareto optimal points (maximize sensitivity, minimize resolution)
    lead_data_sorted = lead_data.sort_values('sensitivity')
    pareto_points = []
    min_resolution = float('inf')
    
    for _, row in lead_data_sorted.iterrows():
        if row['resolution'] < min_resolution:
            pareto_points.append(row)
            min_resolution = row['resolution']
    
    pareto_df = pd.DataFrame(pareto_points)
    
    ax6.scatter(lead_data['sensitivity'], lead_data['resolution'], 
               alpha=0.3, s=30, label='All designs', color='gray')
    ax6.scatter(pareto_df['sensitivity'], pareto_df['resolution'],
               s=100, color='red', label='Pareto optimal', zorder=5)
    ax6.plot(pareto_df['sensitivity'], pareto_df['resolution'],
            'r--', linewidth=2, alpha=0.5)
    
    ax6.set_xlabel('Sensitivity (%)', fontsize=11)
    ax6.set_ylabel('Resolution (mm FWHM)', fontsize=11)
    ax6.set_title('Pareto Front - Optimal Designs', fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('optimization_analysis.png', dpi=300, bbox_inches='tight')
    print("\nOptimization visualization saved as 'optimization_analysis.png'")
    plt.show()
    
    return pareto_df

def find_optimal_designs(df):
    """
    Identify optimal designs based on different criteria
    """
    print("\n" + "="*60)
    print("OPTIMAL DESIGN RECOMMENDATIONS")
    print("="*60)
    
    lead_data = df[df['material'] == 'lead']
    
    # Best sensitivity
    best_sensitivity = lead_data.loc[lead_data['sensitivity'].idxmax()]
    print("\n1. MAXIMUM SENSITIVITY Design:")
    print(f"   Hole Diameter: {best_sensitivity['hole_diameter']:.2f} mm")
    print(f"   Hole Length: {best_sensitivity['hole_length']:.1f} mm")
    print(f"   Sensitivity: {best_sensitivity['sensitivity']:.2f}%")
    print(f"   Resolution: {best_sensitivity['resolution']:.2f} mm")
    
    # Best resolution
    best_resolution = lead_data.loc[lead_data['resolution'].idxmin()]
    print("\n2. BEST RESOLUTION Design:")
    print(f"   Hole Diameter: {best_resolution['hole_diameter']:.2f} mm")
    print(f"   Hole Length: {best_resolution['hole_length']:.1f} mm")
    print(f"   Sensitivity: {best_resolution['sensitivity']:.2f}%")
    print(f"   Resolution: {best_resolution['resolution']:.2f} mm")
    
    # Best figure of merit
    best_fom = lead_data.loc[lead_data['figure_of_merit'].idxmax()]
    print("\n3. BALANCED (Best Figure of Merit) Design:")
    print(f"   Hole Diameter: {best_fom['hole_diameter']:.2f} mm")
    print(f"   Hole Length: {best_fom['hole_length']:.1f} mm")
    print(f"   Sensitivity: {best_fom['sensitivity']:.2f}%")
    print(f"   Resolution: {best_fom['resolution']:.2f} mm")
    print(f"   Figure of Merit: {best_fom['figure_of_merit']:.2f}")
    
    # Clinical recommendations
    print("\n4. CLINICAL RECOMMENDATION (balanced for general purpose):")
    clinical = lead_data[(lead_data['hole_diameter'] >= 1.4) & 
                        (lead_data['hole_diameter'] <= 1.6) &
                        (lead_data['hole_length'] >= 24) &
                        (lead_data['hole_length'] <= 28)]
    
    if len(clinical) > 0:
        best_clinical = clinical.loc[clinical['figure_of_merit'].idxmax()]
        print(f"   Hole Diameter: {best_clinical['hole_diameter']:.2f} mm")
        print(f"   Hole Length: {best_clinical['hole_length']:.1f} mm")
        print(f"   Sensitivity: {best_clinical['sensitivity']:.2f}%")
        print(f"   Resolution: {best_clinical['resolution']:.2f} mm")
    
    print("\n" + "="*60)

def compare_materials(df):
    """
    Compare performance across different materials
    """
    print("\n" + "="*60)
    print("MATERIAL COMPARISON")
    print("="*60)
    
    for material in df['material'].unique():
        material_data = df[df['material'] == material]
        print(f"\n{material.upper()}:")
        print(f"  Average Sensitivity: {material_data['sensitivity'].mean():.2f}%")
        print(f"  Average Resolution: {material_data['resolution'].mean():.2f} mm")
        print(f"  Average Septal Penetration: {material_data['septal_penetration'].mean():.2f}%")
        print(f"  Best Figure of Merit: {material_data['figure_of_merit'].max():.2f}")

def main():
    """
    Main optimization execution
    """
    # Run parameter sweep
    df = parameter_sweep_analysis()
    
    # Save results
    df.to_csv('optimization_results.csv', index=False)
    print("\nResults saved to 'optimization_results.csv'")
    
    # Find optimal designs
    find_optimal_designs(df)
    
    # Compare materials
    compare_materials(df)
    
    # Visualize results
    pareto_df = visualize_optimization_results(df)
    
    # Save Pareto optimal designs
    pareto_df.to_csv('pareto_optimal_designs.csv', index=False)
    print("\nPareto optimal designs saved to 'pareto_optimal_designs.csv'")

if __name__ == "__main__":
    main()