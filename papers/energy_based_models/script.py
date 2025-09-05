# concept_energy_line_demo.py
# ------------------------------------------------------------
# Minimal runnable demo of a relational energy model for a single concept: "line".
# It implements:
#   - Synthetic data generator for the "line" concept
#   - Relational energy network E_theta(x, a, w)
#   - SGLD samplers for x and a
#   - Inner-loop inference of concept codes (w_x, w_a) from few demos
#   - Outer training loop with contrastive + KL-like losses
#   - Qualitative visualization of identification (attention) and generation (entity positions)
#
# HOW TO RUN (Colab or local):
#   !pip install -r requirements.txt   # if needed
#   !python concept_energy_line_demo.py
#
# You can tweak HYPERPARAMS near the top to run faster/slower.
# ------------------------------------------------------------

import math
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import trange, tqdm
import matplotlib.pyplot as plt

# --------------------- HYPERPARAMS ---------------------
SEED = 42
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Scene/event sizes
T = 2              # time steps (x0, x1)
N = 8              # number of entities
DX = 2             # features per entity: 2D position only

# Model
DW = 16            # dimension of concept code w
HIDDEN = 128

# Training
BATCH_SIZE = 128
DEMO_SHOTS = 5     # few-shot demos per concept instance
STEPS = 800        # training iterations (increase to 5000-10000 for better quality)
LR = 1e-3
K_SGLD = 10
ALPHA_X = 1e-2     # SGLD step for x
ALPHA_A = 5e-3     # SGLD step for a
LAMBDA_KL = 1.0

# Eval/visualization
EVAL_BATCH = 1     # visualize a single instance
ATTN_THRESHOLD = 0.5

# --------------------- SEEDING ---------------------
def seed_all(seed:int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

seed_all(SEED)

# --------------------- UTILS ---------------------
def mlp(sizes, act=nn.ReLU, out_act=None):
    layers = []
    for i in range(len(sizes)-1):
        layers += [nn.Linear(sizes[i], sizes[i+1])]
        if i < len(sizes)-2:
            layers += [act()]
        elif out_act is not None:
            layers += [out_act()]
    return nn.Sequential(*layers)

# --------------------- RELATIONAL ENERGY ---------------------
class RelationalEnergy(nn.Module):
    '''
    E_theta(x, a, w) = [ f_theta( sum_{t,i,j} sig(a_i)*sig(a_j) * g_theta([x_t_i, x_t_j, w]), w ) ]^2
    Shapes:
      x: [B, T, N, DX]
      a: [B, N]     (real-valued; gated inside via sigmoid)
      w: [B, DW]
    returns energy: [B]
    '''
    def __init__(self, DX, DW, hidden=128):
        super().__init__()
        self.DX, self.DW = DX, DW
        self.g = mlp([2*DX + DW, hidden, hidden, hidden])
        self.f = mlp([hidden + DW, hidden, hidden, 1])

    def forward(self, x, a, w):
        B, T, N, DX = x.shape
        sig_a = torch.sigmoid(a)                 # [B,N]
        m = sig_a.unsqueeze(2) * sig_a.unsqueeze(1)      # [B,N,N]
        m = m.unsqueeze(1).expand(B, T, N, N)            # [B,T,N,N]

        xi = x.unsqueeze(3).expand(B, T, N, N, DX)       # [B,T,N,N,DX]
        xj = x.unsqueeze(2).expand(B, T, N, N, DX)       # [B,T,N,N,DX]
        w_exp = w.view(B,1,1,1,-1).expand(B,T,N,N,-1)    # [B,T,N,N,DW]
        pair_feat = torch.cat([xi, xj, w_exp], dim=-1)   # [B,T,N,N,2DX+DW]

        g_ij = self.g(pair_feat)                         # [B,T,N,N,H]
        g_ij = g_ij * m.unsqueeze(-1)                    # gate by attention pairs
        pooled = g_ij.sum(dim=(1,2,3))                   # [B,H]

        f_in = torch.cat([pooled, w], dim=-1)            # [B,H+DW]
        out = self.f(f_in).squeeze(-1)                   # [B]
        energy = out.pow(2)                               # non-negative
        return energy

# --------------------- SGLD ---------------------
def sgld_step(var, grad, alpha):
    noise = torch.randn_like(var) * (alpha ** 0.5)
    return var + 0.5 * alpha * grad + noise

@torch.no_grad()
def sgld_optimize_x(E, x_init, a, w, steps=10, alpha=1e-2):
    x = x_init.clone().requires_grad_(True)
    for _ in range(steps):
        E_x = E(x, a, w).sum()
        grad, = torch.autograd.grad(E_x, x, create_graph=False)
        x = sgld_step(x, grad, alpha).detach().requires_grad_(True)
    return x.detach()

@torch.no_grad()
def sgld_optimize_a(E, x, a_init, w, steps=10, alpha=1e-2):
    a = a_init.clone().requires_grad_(True)
    for _ in range(steps):
        E_a = E(x, a, w).sum()
        grad, = torch.autograd.grad(E_a, a, create_graph=False)
        a = sgld_step(a, grad, alpha).detach().requires_grad_(True)
    return a.detach()

# --------------------- CONCEPT-CODE INFERENCE ---------------------
def infer_concept_codes(E, demos, DW, steps=10, lr=0.1):
    '''
    demos keys: x0, x1, a (each [B,T,N,DX], [B,T,N,DX], [B,N])
    Returns: w_x, w_a [B, DW]
    '''
    B = demos['x0'].shape[0]
    w_x = torch.randn(B, DW, device=demos['x0'].device, requires_grad=True)
    w_a = torch.randn(B, DW, device=demos['x0'].device, requires_grad=True)
    opt = torch.optim.SGD([w_x, w_a], lr=lr)

    for _ in range(steps):
        opt.zero_grad()
        Ex = E(demos['x1'], demos['a'], w_x)
        Ea = E(demos['x0'], demos['a'], w_a)
        loss = (Ex + Ea).mean()
        loss.backward()
        opt.step()
    return w_x.detach(), w_a.detach()

# --------------------- DATA: "LINE" CONCEPT ---------------------
def sample_line_batch(B, T, N, DX=2, noise=0.02, length=1.6, k_attend=4, device="cpu"):
    '''
    Returns a dict with x0, x1, a (tensors).
    - x0: random initial positions in [-1,1]^2 at t=0, and near a line at t=1 for attended entities
    - a: real-valued attention where attended indices have larger positive values
    - x1: equal to x0 here (T=2 frames, last is the "after" state)
    '''
    x = torch.empty(B, T, N, DX, device=device)

    # t=0 random in [-1,1], t=1 start as copy
    x[:, 0] = torch.rand(B, N, DX, device=device) * 2 - 1
    x[:, 1] = x[:, 0].clone()

    a = torch.zeros(B, N, device=device)

    for b in range(B):
        idx = torch.randperm(N, device=device)[:k_attend]
        a[b, idx] = 3.0  # positive => sigmoid(a) ~ 0.95

        # construct a random line at t=1: p0 + t * dir
        p0 = torch.rand(2, device=device) * 2 - 1
        direction = torch.rand(2, device=device) * 2 - 1
        direction = direction / (direction.norm() + 1e-8)
        t_vals = torch.linspace(-length/2, length/2, k_attend, device=device)
        line_pts = p0 + t_vals[:, None] * direction
        x[b, 1, idx, :2] = line_pts + noise * torch.randn_like(line_pts)

        # non-attended can move slightly/randomly between frames
        others = torch.tensor([i for i in range(N) if i not in idx], device=device)
        x[b, 1, others, :2] = x[b, 0, others, :2] + 0.05 * torch.randn_like(x[b, 0, others, :2])

    return {"x0": x[:, :1].repeat(1, T, 1, 1),  # keep 2 frames for interface consistency
            "x1": x,
            "a": a}

class LineConceptDataset(Dataset):
    def __init__(self, num_samples=10_000, device="cpu"):
        self.num_samples = num_samples
        self.device = device

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        # Each __getitem__ returns a fresh synthetic sample (concept instance)
        batch = sample_line_batch(1, T=T, N=N, DX=DX, device=self.device)
        return {k: v.squeeze(0) for k, v in batch.items()}  # remove batch dim

def collate(batch_list):
    # Stack single-sample dicts into batch tensors
    out = {}
    for k in batch_list[0]:
        out[k] = torch.stack([b[k] for b in batch_list], dim=0)
    return out

# --------------------- TRAINING LOOP ---------------------
def training_step(E, batch_demo, batch_train, opt_theta, K=10, alpha_x=1e-2, alpha_a=5e-3, lam=1.0):
    # 1) infer w's from demos (stop-grad on theta for simplicity)
    with torch.no_grad():
        w_x, w_a = infer_concept_codes(E, batch_demo, DW=DW, steps=K, lr=0.1)

    # 2) sample negatives
    x0, x1, a = batch_train['x0'], batch_train['x1'], batch_train['a']
    a_init = torch.randn_like(a)
    x_tilde = sgld_optimize_x(E, x0, a, w_x, steps=K, alpha=alpha_x)
    a_tilde = sgld_optimize_a(E, x0, a_init, w_a, steps=K, alpha=alpha_a)

    # 3) losses
    Ex_pos = E(x1, a, w_x)
    Ex_neg = E(x_tilde, a, w_x)
    Ea_pos = E(x0, a, w_a)
    Ea_neg = E(x0, a_tilde, w_a)

    Lx = F.softplus(Ex_pos - Ex_neg).mean()
    La = F.softplus(Ea_pos - Ea_neg).mean()
    L_ml = Lx + La

    L_kl = (Ex_neg + Ea_neg).mean()

    loss = L_ml + lam * L_kl

    opt_theta.zero_grad(set_to_none=True)
    loss.backward()
    nn.utils.clip_grad_norm_(E.parameters(), 1.0)
    opt_theta.step()

    return {
        "loss": loss.item(),
        "L_ml": L_ml.item(),
        "L_kl": L_kl.item(),
        "Ex_pos": Ex_pos.mean().item(),
        "Ex_neg": Ex_neg.mean().item(),
        "Ea_pos": Ea_pos.mean().item(),
        "Ea_neg": Ea_neg.mean().item(),
    }

def make_demo_batch(dataset, shots=5, device="cpu"):
    # sample K shots and stack into a demo batch
    items = [dataset[random.randrange(len(dataset))] for _ in range(shots)]
    demo = collate(items)
    # Ensure x0 has T frames (we already store with 2 frames)
    for k in demo:
        demo[k] = demo[k].to(device)
    return demo

def main():
    print(f"Using device: {DEVICE}")
    ds = LineConceptDataset(num_samples=50_000, device=DEVICE)
    dl = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate, drop_last=True)

    E = RelationalEnergy(DX, DW, hidden=HIDDEN).to(DEVICE)
    opt = torch.optim.Adam(E.parameters(), lr=LR)

    pbar = trange(STEPS, desc="Training")
    running = {}
    for step in pbar:
        # Make a fresh demo set (few-shot) from same distribution
        demo = make_demo_batch(ds, shots=DEMO_SHOTS, device=DEVICE)
        global dl_iter
        # One training batch
        try:
            batch = next(dl_iter)
        except NameError:
            pass
        except StopIteration:
            pass
        # Use an iterator to avoid resetting shuffle every time
        
        try:
            batch = next(dl_iter)
        except:
            dl_iter = iter(dl)
            batch = next(dl_iter)

        for k in batch:
            batch[k] = batch[k].to(DEVICE)

        logs = training_step(E, demo, batch, opt, K=K_SGLD, alpha_x=ALPHA_X, alpha_a=ALPHA_A, lam=LAMBDA_KL)
        for k,v in logs.items():
            running[k] = 0.97*running.get(k, v) + 0.03*v  # EMA for display
        pbar.set_postfix({k: f"{running[k]:.3f}" for k in ["loss","L_ml","L_kl"]})

    # --------------------- QUALITATIVE EVALUATION ---------------------
    E.eval()
    with torch.no_grad():
        demo = make_demo_batch(ds, shots=DEMO_SHOTS, device=DEVICE)
        w_x, w_a = infer_concept_codes(E, demo, DW=DW, steps=K_SGLD, lr=0.1)

        # Take a fresh eval instance
        eval_sample = collate([ds[0] for _ in range(EVAL_BATCH)])
        for k in eval_sample: eval_sample[k] = eval_sample[k].to(DEVICE)

    # Identification: infer a via SGLD with x fixed
    a_init = torch.randn_like(eval_sample["a"])
    a_tilde = sgld_optimize_a(E, eval_sample["x0"], a_init, w_a[:EVAL_BATCH], steps=K_SGLD, alpha=ALPHA_A)
    a_prob = torch.sigmoid(a_tilde)[0].detach().cpu().numpy()

    # Generation: infer x1 given a fixed attention (use the ground-truth attention as a demonstration)
    x_tilde = sgld_optimize_x(E, eval_sample["x0"], eval_sample["a"], w_x[:EVAL_BATCH], steps=K_SGLD, alpha=ALPHA_X)
    x0_np = eval_sample["x0"][0, 0, :, :2].detach().cpu().numpy()
    x1_np = x_tilde[0, 1, :, :2].detach().cpu().numpy()

    # --------------------- PLOTS ---------------------
    # 1) Attention bar plot (identification)
    plt.figure()
    plt.title("Identification: inferred attention probabilities per entity")
    plt.bar(np.arange(N), a_prob)
    plt.xlabel("Entity index")
    plt.ylabel("sigmoid(a)")
    plt.ylim(0, 1.0)
    plt.tight_layout()
    plt.savefig("identification_attention.png")

    # 2) Generation scatter plot: initial vs generated final positions
    plt.figure()
    plt.title("Generation: initial (t=0) vs generated final (t=1) positions")
    plt.scatter(x0_np[:,0], x0_np[:,1], label="t=0")
    plt.scatter(x1_np[:,0], x1_np[:,1], label="generated t=1", marker="x")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.legend()
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig("generation_positions.png")

    print("Saved figures: identification_attention.png, generation_positions.png")
    print("Done.")

if __name__ == "__main__":
    main()
