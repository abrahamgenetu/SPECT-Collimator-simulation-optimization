"""
SPECT Collimator Simulation and Optimization
Monte Carlo simulation of gamma-ray photon transport through parallel-hole collimators

Author: [Your Name]
Date: November 2025
Purpose: Demonstrate nuclear imaging hardware engineering skills for Siemens Healthineers position
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from dataclasses import dataclass
import json

@dataclass
class CollimatorParams:
    """Parameters defining collimator geometry and material"""
    hole_diameter: float  # mm
    hole_length: float    # mm
    septal_thickness: float  # mm
    material: str
    num_holes_x: int = 100
    num_holes_y: int = 100
    
@dataclass
class MaterialProperties:
    """Material properties for different collimator materials"""
    density: float  # g/cm³
    attenuation_coefficient: float  # cm⁻¹ at 140 keV (Tc-99m)
    name: str

# Material database
MATERIALS = {
    'lead': MaterialProperties(11.34, 23.0, 'Lead'),
    'tungsten': MaterialProperties(19.25, 18.0, 'Tungsten'),
    'brass': MaterialProperties(8.5, 8.0, 'Brass')
}

class SPECTSimulator:
    """Monte Carlo simulator for SPECT collimator performance"""
    
    def __init__(self, params: CollimatorParams):
        self.params = params
        self.material = MATERIALS[params.material]
        
    def simulate_photon_transport(self, num_photons: int = 10000, source_distance: float = 100.0):
        """
        Simulate photon transport through collimator
        
        Args:
            num_photons: Number of photons to simulate
            source_distance: Distance from source to collimator face (mm)
            
        Returns:
            dict containing detected photons and statistics
        """
        detected_photons = []
        septal_penetration_count = 0
        geometric_rejection_count = 0
        
        # Detector dimensions
        detector_width = self.params.num_holes_x * (self.params.hole_diameter + self.params.septal_thickness)
        detector_height = self.params.num_holes_y * (self.params.hole_diameter + self.params.septal_thickness)
        
        for _ in range(num_photons):
            # Generate random photon from point source
            theta = np.random.uniform(-np.pi/6, np.pi/6)  # Angle from normal
            phi = np.random.uniform(0, 2*np.pi)  # Azimuthal angle
            
            # Initial position at collimator face
            x0 = np.random.uniform(-detector_width/2, detector_width/2)
            y0 = np.random.uniform(-detector_height/2, detector_height/2)
            
            # Direction cosines
            dx = np.sin(theta) * np.cos(phi)
            dy = np.sin(theta) * np.sin(phi)
            dz = np.cos(theta)
            
            # Calculate which hole the photon enters
            hole_x_idx = int((x0 + detector_width/2) / (self.params.hole_diameter + self.params.septal_thickness))
            hole_y_idx = int((y0 + detector_height/2) / (self.params.hole_diameter + self.params.septal_thickness))
            
            # Check geometric acceptance
            acceptance_angle = np.arctan(self.params.hole_diameter / (2 * self.params.hole_length))
            
            if abs(theta) > acceptance_angle:
                geometric_rejection_count += 1
                continue
            
            # Calculate path length through collimator
            path_length = self.params.hole_length / np.cos(theta) if np.cos(theta) > 0 else np.inf
            
            # Calculate interaction with septa
            septal_path_length = self._calculate_septal_path(theta, phi)
            
            # Attenuation probability (Beer-Lambert law)
            attenuation_prob = np.exp(-self.material.attenuation_coefficient * septal_path_length / 10)  # Convert to cm
            
            if np.random.random() > attenuation_prob:
                septal_penetration_count += 1
                continue
            
            # Photon reaches detector
            x_final = x0 + dx * self.params.hole_length / dz
            y_final = y0 + dy * self.params.hole_length / dz
            
            # Energy with realistic energy resolution (10% FWHM at 140 keV)
            energy = np.random.normal(140, 140 * 0.1 / 2.355)
            
            detected_photons.append({
                'x': x_final,
                'y': y_final,
                'energy': energy
            })
        
        return {
            'detected_photons': detected_photons,
            'total_photons': num_photons,
            'detected_count': len(detected_photons),
            'septal_penetration': septal_penetration_count,
            'geometric_rejection': geometric_rejection_count
        }
    
    def _calculate_septal_path(self, theta, phi):
        """Calculate path length through septal walls"""
        if abs(theta) < 1e-6:
            return 0.0
        
        # Simplified calculation - assumes photon might graze septa
        max_septal_interaction = self.params.septal_thickness * abs(np.tan(theta))
        return max_septal_interaction
    
    def calculate_metrics(self, simulation_results):
        """
        Calculate image quality metrics from simulation results
        
        Returns:
            dict of performance metrics
        """
        photons = simulation_results['detected_photons']
        total = simulation_results['total_photons']
        
        if len(photons) == 0:
            return {
                'sensitivity': 0.0,
                'spatial_resolution_fwhm': 0.0,
                'uniformity': 0.0,
                'contrast_to_noise': 0.0
            }
        
        # Sensitivity (geometric efficiency)
        sensitivity = len(photons) / total * 100
        
        # Spatial resolution (FWHM)
        x_positions = np.array([p['x'] for p in photons])
        spatial_resolution = self._calculate_fwhm(x_positions)
        
        # Uniformity
        uniformity = self._calculate_uniformity(photons)
        
        # Contrast-to-noise ratio (simplified)
        cnr = np.sqrt(len(photons)) if len(photons) > 0 else 0
        
        return {
            'sensitivity': sensitivity,
            'spatial_resolution_fwhm': spatial_resolution,
            'uniformity': uniformity,
            'contrast_to_noise': cnr,
            'septal_penetration_fraction': simulation_results['septal_penetration'] / total * 100,
            'geometric_efficiency': (total - simulation_results['geometric_rejection']) / total * 100
        }
    
    def _calculate_fwhm(self, positions):
        """Calculate Full Width at Half Maximum"""
        if len(positions) < 10:
            return 0.0
        
        std_dev = np.std(positions)
        fwhm = 2.355 * std_dev  # Conversion factor for Gaussian
        return fwhm
    
    def _calculate_uniformity(self, photons, grid_size=10):
        """Calculate uniformity using coefficient of variation"""
        if len(photons) < 10:
            return 0.0
        
        # Create 2D histogram
        x = np.array([p['x'] for p in photons])
        y = np.array([p['y'] for p in photons])
        
        hist, _, _ = np.histogram2d(x, y, bins=grid_size)
        
        # Calculate uniformity as 1 - CV (coefficient of variation)
        mean_counts = np.mean(hist)
        std_counts = np.std(hist)
        
        if mean_counts > 0:
            uniformity = (1 - std_counts / mean_counts) * 100
            return max(0, uniformity)
        return 0.0

def optimize_collimator(param_ranges, num_photons=5000):
    """
    Optimize collimator design by sweeping parameter space
    
    Args:
        param_ranges: dict with parameter names and (min, max, steps) tuples
        num_photons: number of photons per simulation
        
    Returns:
        list of results for each parameter combination
    """
    results = []
    
    # Generate parameter combinations
    hole_diameters = np.linspace(*param_ranges['hole_diameter'])
    hole_lengths = np.linspace(*param_ranges['hole_length'])
    
    for diameter in hole_diameters:
        for length in hole_lengths:
            params = CollimatorParams(
                hole_diameter=diameter,
                hole_length=length,
                septal_thickness=0.2,
                material='lead'
            )
            
            sim = SPECTSimulator(params)
            sim_results = sim.simulate_photon_transport(num_photons)
            metrics = sim.calculate_metrics(sim_results)
            
            results.append({
                'hole_diameter': diameter,
                'hole_length': length,
                'sensitivity': metrics['sensitivity'],
                'spatial_resolution': metrics['spatial_resolution_fwhm'],
                'uniformity': metrics['uniformity']
            })
            
            print(f"Diameter: {diameter:.2f}mm, Length: {length:.1f}mm -> "
                  f"Sensitivity: {metrics['sensitivity']:.2f}%, "
                  f"Resolution: {metrics['spatial_resolution_fwhm']:.2f}mm")
    
    return results

def visualize_results(simulation_results, metrics):
    """Create visualization of simulation results"""
    photons = simulation_results['detected_photons']
    
    if len(photons) == 0:
        print("No photons detected - cannot visualize")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # 1. Planar image (2D histogram)
    x = np.array([p['x'] for p in photons])
    y = np.array([p['y'] for p in photons])
    
    axes[0, 0].hist2d(x, y, bins=50, cmap='hot')
    axes[0, 0].set_title('Planar Detector Image', fontsize=14, fontweight='bold')
    axes[0, 0].set_xlabel('X Position (mm)')
    axes[0, 0].set_ylabel('Y Position (mm)')
    axes[0, 0].set_aspect('equal')
    
    # 2. Energy spectrum
    energies = np.array([p['energy'] for p in photons])
    axes[0, 1].hist(energies, bins=50, color='blue', alpha=0.7, edgecolor='black')
    axes[0, 1].set_title('Energy Spectrum', fontsize=14, fontweight='bold')
    axes[0, 1].set_xlabel('Energy (keV)')
    axes[0, 1].set_ylabel('Counts')
    axes[0, 1].axvline(140, color='red', linestyle='--', linewidth=2, label='140 keV (Tc-99m)')
    axes[0, 1].legend()
    
    # 3. Spatial resolution profile
    profile = np.histogram(x, bins=100)[0]
    axes[1, 0].plot(profile, linewidth=2)
    axes[1, 0].set_title(f'Spatial Resolution Profile\nFWHM: {metrics["spatial_resolution_fwhm"]:.2f} mm', 
                        fontsize=14, fontweight='bold')
    axes[1, 0].set_xlabel('Bin Number')
    axes[1, 0].set_ylabel('Counts')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Performance metrics
    axes[1, 1].axis('off')
    metrics_text = f"""
    Performance Metrics
    ═══════════════════════════
    
    Sensitivity: {metrics['sensitivity']:.2f}%
    
    Spatial Resolution (FWHM): {metrics['spatial_resolution_fwhm']:.2f} mm
    
    Uniformity: {metrics['uniformity']:.2f}%
    
    Contrast-to-Noise: {metrics['contrast_to_noise']:.1f}
    
    Geometric Efficiency: {metrics['geometric_efficiency']:.2f}%
    
    Septal Penetration: {metrics['septal_penetration_fraction']:.2f}%
    
    Detected Photons: {simulation_results['detected_count']:,}
    """
    axes[1, 1].text(0.1, 0.5, metrics_text, fontsize=12, family='monospace',
                   verticalalignment='center')
    
    plt.tight_layout()
    plt.savefig('simulation_results.png', dpi=300, bbox_inches='tight')
    print("\nVisualization saved as 'simulation_results.png'")
    plt.show()

def main():
    """Main execution function"""
    print("="*60)
    print("SPECT Collimator Simulation and Optimization")
    print("="*60)
    
    # Define collimator parameters
    params = CollimatorParams(
        hole_diameter=1.5,  # mm
        hole_length=25.0,   # mm
        septal_thickness=0.2,  # mm
        material='lead'
    )
    
    print(f"\nCollimator Configuration:")
    print(f"  Hole Diameter: {params.hole_diameter} mm")
    print(f"  Hole Length: {params.hole_length} mm")
    print(f"  Septal Thickness: {params.septal_thickness} mm")
    print(f"  Material: {MATERIALS[params.material].name}")
    
    # Run simulation
    print(f"\nRunning Monte Carlo simulation with 10,000 photons...")
    simulator = SPECTSimulator(params)
    results = simulator.simulate_photon_transport(num_photons=10000)
    
    # Calculate metrics
    metrics = simulator.calculate_metrics(results)
    
    print(f"\nSimulation Results:")
    print(f"  Detected Photons: {results['detected_count']:,} / {results['total_photons']:,}")
    print(f"  Sensitivity: {metrics['sensitivity']:.2f}%")
    print(f"  Spatial Resolution: {metrics['spatial_resolution_fwhm']:.2f} mm FWHM")
    print(f"  Uniformity: {metrics['uniformity']:.2f}%")
    print(f"  Contrast-to-Noise: {metrics['contrast_to_noise']:.1f}")
    
    # Visualize results
    visualize_results(results, metrics)
    
    # Save results to JSON
    output_data = {
        'parameters': {
            'hole_diameter': params.hole_diameter,
            'hole_length': params.hole_length,
            'septal_thickness': params.septal_thickness,
            'material': params.material
        },
        'metrics': metrics,
        'simulation_info': {
            'total_photons': results['total_photons'],
            'detected_photons': results['detected_count']
        }
    }
    
    with open('simulation_results.json', 'w') as f:
        json.dump(output_data, f, indent=2)
    print("\nResults saved to 'simulation_results.json'")

if __name__ == "__main__":
    main()