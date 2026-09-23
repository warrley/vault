#!/home/warley/.venv/pinn-gpu/bin/python3
"""
Orquestrador Principal de Treinamento e Avaliação — Paper 1 (Calor 2D e Burgers 2D)
Executa em sequência:
  1. Equação do Calor 2D Transiente (20.000 épocas, modelo exato C^infty)
  2. Equação de Burgers 2D Viscosa (20.000 épocas, referência RK4 de alta resolução)
Gera modelos .pth, curvas de perda de alta resolução, figuras 3D e 2D, e linhas de tabela LaTeX.
"""

import os
import sys
import time
import subprocess

def get_python_interpreter():
    pinn_gpu_py = "/home/warley/.venv/pinn-gpu/bin/python3"
    if os.path.exists(pinn_gpu_py):
        return pinn_gpu_py
    return sys.executable

def main():
    print("="*80)
    print("ORQUESTRADOR DE EXPERIMENTOS PINN — PAPER 1 (HEAT & BURGERS 2D)")
    print("="*80)
    
    overall_start = time.time()
    
    # Obter diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    heat_script = os.path.join(script_dir, "train_heat_2d.py")
    burgers_script = os.path.join(script_dir, "train_burgers_2d.py")
    
    py_bin = get_python_interpreter()
    print(f"Interpretador Python: {py_bin}")
    
    # 1. Execução do Calor 2D
    print("\n[ETAPA 1/2] Iniciando Treinamento e Avaliação: Equação do Calor 2D...", flush=True)
    t0_heat = time.time()
    res_heat = subprocess.run([py_bin, "-u", heat_script])
    dur_heat = time.time() - t0_heat
    if res_heat.returncode != 0:
        print(f"\n[ERRO] Falha na execução do Calor 2D (código {res_heat.returncode}).", flush=True)
        sys.exit(res_heat.returncode)
    print(f"[CONCLUÍDO] Calor 2D finalizado com sucesso em {dur_heat:.2f}s ({dur_heat/60:.2f} min).", flush=True)
    
    # 2. Execução de Burgers 2D
    print("\n" + "-"*80, flush=True)
    print("[ETAPA 2/2] Iniciando Treinamento e Avaliação: Equação de Burgers 2D...", flush=True)
    t0_burg = time.time()
    res_burg = subprocess.run([py_bin, "-u", burgers_script])
    dur_burg = time.time() - t0_burg
    if res_burg.returncode != 0:
        print(f"\n[ERRO] Falha na execução de Burgers 2D (código {res_burg.returncode}).", flush=True)
        sys.exit(res_burg.returncode)
    print(f"[CONCLUÍDO] Burgers 2D finalizado com sucesso em {dur_burg:.2f}s ({dur_burg/60:.2f} min).", flush=True)
    
    total_time = time.time() - overall_start
    print("\n" + "="*80)
    print("EXECUÇÃO COMPLETA DE TODOS OS MODELOS FINALIZADA COM SUCESSO!")
    print("="*80)
    print(f"Tempo Total de Processamento: {total_time:.2f} s ({total_time/60:.2f} min)")
    print(f"  - Tempo Calor 2D:    {dur_heat:.2f} s ({dur_heat/60:.2f} min)")
    print(f"  - Tempo Burgers 2D:  {dur_burg:.2f} s ({dur_burg/60:.2f} min)")
    print("\nArtefatos gerados:")
    print("  - Modelos (.pth): ./paper1_heat_burgers/models/")
    print("  - Figuras (.pdf / .png): ./paper1_heat_burgers/figures/")
    print("="*80)

if __name__ == '__main__':
    main()
