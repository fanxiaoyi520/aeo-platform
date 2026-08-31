# 通用 SKU 试点测试集（S7-01）

| 属性 | 值 |
|------|-----|
| **任务** | S7-01 |
| **里程碑** | MS7 |
| **机器可读** | [`aeo-platform/pilot/sample-sku-testset.json`](../../aeo-platform/pilot/sample-sku-testset.json) |
| **条目数** | 20 SKU |

---

## 选取原则

1. **品类多样性** — 消费电子、家居、厨房、美妆、宠物等常见跨境品类
2. **平台分布** — Amazon US 16 项，TikTok US 4 项
3. **降级路径** — 至少 5 项无竞品 ASIN，测试 research 降级
4. **RAG 映射** — 3 项映射 `knowledge/products/sample-product.md`；其余依赖平台规则 + 关键词

---

## SKU 清单（摘要）

| ID | SKU | 产品名 | 平台 | 产品线 | 竞品 ASIN |
|----|-----|--------|------|--------|-----------|
| SMP-001 | ACME-EARBUDS-PRO | Acme Wireless Earbuds Pro | amazon | Audio | 2 |
| SMP-002 | ACME-EARBUDS-LITE | Acme Wireless Earbuds Lite | amazon | Audio | 2 |
| SMP-003 | ACME-HEADPHONE-ANC | Acme Over-Ear Headphones ANC | amazon | Audio | 1 |
| SMP-004 | HOMEBREW-KETTLE-1L | HomeBrew Electric Kettle 1L | amazon | Home | 2 |
| SMP-005 | HOMEBREW-VACUUM-S | HomeBrew Cordless Vacuum S | amazon | Home | 1 |
| SMP-006 | KITCHEN-AIRFRYER-4QT | KitchenPro Air Fryer 4QT | amazon | Kitchen | 2 |
| SMP-007 | KITCHEN-BLENDER-PRO | KitchenPro Blender Pro | amazon | Kitchen | 1 |
| SMP-008 | GLOW-HAIRDRYER-ION | GlowCare Ionic Hair Dryer | amazon | Beauty | 1 |
| SMP-009 | GLOW-FACIAL-BRUSH | GlowCare Facial Cleansing Brush | amazon | Beauty | 1 |
| SMP-010 | TECH-POWERBANK-20K | TechNova Power Bank 20000mAh | amazon | Electronics | 1 |
| SMP-011 | TECH-MONITOR-24 | TechNova 24 Inch Monitor | amazon | Electronics | 1 |
| SMP-012 | FIT-TRACKER-BAND | FitPulse Activity Tracker Band | amazon | Wearables | 1 |
| SMP-013 | PET-WATER-FOUNTAIN | PetPal Cat Water Fountain | amazon | Pet | 1 |
| SMP-014 | OFFICE-DESK-LAMP | OfficeGlow LED Desk Lamp | amazon | Office | 0 |
| SMP-015 | OUTDOOR-CAMP-LANTERN | TrailMax Camping Lantern | amazon | Outdoor | 0 |
| SMP-016 | BABY-MONITOR-HD | TinyGuard Baby Monitor HD | amazon | Baby | 0 |
| SMP-017 | ACME-EARBUDS-TK | Acme Wireless Earbuds Pro | tiktok | Audio | 0 |
| SMP-018 | KITCHEN-AIRFRYER-TK | KitchenPro Air Fryer 4QT | tiktok | Kitchen | 0 |
| SMP-019 | GLOW-HAIRDRYER-TK | GlowCare Ionic Hair Dryer | tiktok | Beauty | 0 |
| SMP-020 | TECH-POWERBANK-TK | TechNova Power Bank 20000mAh | tiktok | Electronics | 0 |

---

## 创建任务示例 payload

```json
{
  "sku": "ACME-EARBUDS-PRO",
  "platform": "amazon",
  "market": "US",
  "product_info": {
    "competitor_asins": ["B09XS7JWHH", "B0BZPL12X2"],
    "keywords": ["wireless earbuds", "noise cancelling", "bluetooth 5.3"]
  }
}
```

## 批跑

```powershell
cd aeo-platform
.\scripts\batch_pilot.ps1 --dry-run
```
