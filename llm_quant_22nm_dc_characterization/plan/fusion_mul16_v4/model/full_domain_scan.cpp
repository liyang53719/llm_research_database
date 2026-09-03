#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>

namespace fs = std::filesystem;

struct FPOperand {
  int sign;
  int sig;
  int scale;
  bool zero;
  bool inf;
  bool nan;
};

static int msb_index(uint32_t x) {
  assert(x != 0);
  int msb = 0;
  while (x >>= 1) ++msb;
  return msb;
}

static uint16_t pack_rtl(int sign, uint32_t raw, int scale,
                         bool zero=false, bool inf=false, bool nan=false) {
  sign &= 1;
  if (nan) return static_cast<uint16_t>((sign << 15) | 0x7fc0);
  if (inf) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  if (zero || raw == 0) return static_cast<uint16_t>(sign << 15);

  int msb = msb_index(raw);
  int exponent = scale + msb;
  if (exponent > 127) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  if (exponent < -126) return static_cast<uint16_t>(sign << 15);

  uint32_t sig8 = 0;
  if (msb > 7) {
    int shift = msb - 7;
    sig8 = raw >> shift;
    uint32_t guard = (raw >> (shift - 1)) & 1u;
    uint32_t sticky_mask = shift > 1 ? ((1u << (shift - 1)) - 1u) : 0u;
    bool sticky = (raw & sticky_mask) != 0;
    bool round_up = guard && (sticky || (sig8 & 1u));
    uint32_t rounded = sig8 + static_cast<uint32_t>(round_up);
    if (rounded & 0x100u) {
      sig8 = rounded >> 1;
      ++exponent;
    } else {
      sig8 = rounded;
    }
  } else {
    sig8 = raw << (7 - msb);
  }
  if (exponent > 127) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  return static_cast<uint16_t>((sign << 15) | ((exponent + 127) << 7) | (sig8 & 0x7f));
}

static uint16_t pack_reference(int sign, uint32_t raw, int scale,
                               bool zero=false, bool inf=false, bool nan=false) {
  sign &= 1;
  if (nan) return static_cast<uint16_t>((sign << 15) | 0x7fc0);
  if (inf) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  if (zero || raw == 0) return static_cast<uint16_t>(sign << 15);

  int msb = msb_index(raw);
  int exponent = scale + msb;
  if (exponent > 127) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  if (exponent < -126) return static_cast<uint16_t>(sign << 15);

  uint32_t quotient = 0;
  if (msb <= 7) {
    quotient = raw << (7 - msb);
  } else {
    uint32_t divisor = 1u << (msb - 7);
    quotient = raw / divisor;
    uint32_t remainder = raw % divisor;
    uint64_t twice = static_cast<uint64_t>(remainder) * 2u;
    bool increment = twice > divisor || (twice == divisor && (quotient & 1u));
    quotient += static_cast<uint32_t>(increment);
    if (quotient >= 256u) {
      quotient >>= 1;
      ++exponent;
    }
  }
  if (exponent > 127) return static_cast<uint16_t>((sign << 15) | 0x7f80);
  return static_cast<uint16_t>((sign << 15) | ((exponent + 127) << 7) | (quotient & 0x7f));
}

static FPOperand decode_fp8(uint8_t raw) {
  int exp = (raw >> 3) & 0xf;
  int frac = raw & 7;
  return FPOperand{(raw >> 7) & 1, exp == 0 ? frac : 8 | frac,
                   exp == 0 ? -9 : exp - 10,
                   exp == 0 && frac == 0, false, exp == 15 && frac == 7};
}

static FPOperand decode_bf16(uint16_t raw) {
  int exp = (raw >> 7) & 0xff;
  int frac = raw & 0x7f;
  return FPOperand{(raw >> 15) & 1, exp == 0 ? frac : 128 | frac,
                   exp == 0 ? -133 : exp - 134,
                   exp == 0 && frac == 0,
                   exp == 255 && frac == 0,
                   exp == 255 && frac != 0};
}

static uint16_t product(const FPOperand& a, const FPOperand& b, bool reference) {
  bool zero = a.zero || b.zero;
  bool inf = (a.inf || b.inf) && !zero;
  bool nan = a.nan || b.nan || (zero && (a.inf || b.inf));
  auto fn = reference ? pack_reference : pack_rtl;
  return fn(a.sign ^ b.sign, static_cast<uint32_t>(a.sig * b.sig),
            a.scale + b.scale, zero, inf, nan);
}

static bool equivalent(uint16_t a, uint16_t b) {
  bool a_nan = (a & 0x7f80u) == 0x7f80u && (a & 0x7fu) != 0;
  bool b_nan = (b & 0x7f80u) == 0x7f80u && (b & 0x7fu) != 0;
  return (a_nan && b_nan) || a == b;
}

struct Result {
  std::string mode;
  std::string coverage_kind;
  uint64_t checks;
  uint64_t raw_pair_space;
  uint64_t mismatches;
  uint64_t finite_equivalence_checks = 0;
  uint64_t special_representative_checks = 0;
};

static void verify(const std::string& name, uint16_t got, uint16_t expected,
                   uint64_t& checks, uint64_t& mismatches) {
  ++checks;
  if (!equivalent(got, expected)) {
    if (mismatches < 8) {
      std::cerr << name << " mismatch got=0x" << std::hex << got
                << " expected=0x" << expected << std::dec << "\n";
    }
    ++mismatches;
  }
}

static std::set<uint32_t> product_set(int a_lo, int a_hi, int b_lo, int b_hi) {
  std::set<uint32_t> out;
  for (int a=a_lo; a<=a_hi; ++a)
    for (int b=b_lo; b<=b_hi; ++b)
      out.insert(static_cast<uint32_t>(a*b));
  return out;
}

static Result scan_i4_i8() {
  Result r{"i4_i8","literal_exhaustive_pairs",0,16ull*256ull,0};
  for (int a=-8;a<=7;++a) for (int b=-128;b<=127;++b) {
    int am=std::abs(a), bm=std::abs(b);
    int mag=am*(bm&15)+(am*(bm>>4)<<4);
    int got=((a<0)^(b<0))?-mag:mag;
    ++r.checks; if(got!=a*b) ++r.mismatches;
  }
  return r;
}

static Result scan_i8_i8() {
  Result r{"i8_i8","literal_exhaustive_pairs",0,256ull*256ull,0};
  for(int a=-128;a<=127;++a) for(int b=-128;b<=127;++b) {
    int am=std::abs(a),bm=std::abs(b);
    int mag=(am&15)*(bm&15)+((am&15)*(bm>>4)<<4)+((am>>4)*(bm&15)<<4)+((am>>4)*(bm>>4)<<8);
    int got=((a<0)^(b<0))?-mag:mag;
    ++r.checks; if(got!=a*b) ++r.mismatches;
  }
  return r;
}

static Result scan_fp8_fp8() {
  Result r{"fp8_fp8","literal_exhaustive_raw_pairs",0,256ull*256ull,0};
  for(int a=0;a<256;++a) for(int b=0;b<256;++b)
    verify(r.mode,product(decode_fp8(a),decode_fp8(b),false),product(decode_fp8(a),decode_fp8(b),true),r.checks,r.mismatches);
  return r;
}

static Result scan_i4_fp8() {
  Result r{"i4_fp8","literal_exhaustive_raw_pairs",0,16ull*256ull,0};
  for(int a=-8;a<=7;++a) for(int b=0;b<256;++b) {
    FPOperand ai{a<0,std::abs(a),0,a==0,false,false};
    verify(r.mode,product(ai,decode_fp8(b),false),product(ai,decode_fp8(b),true),r.checks,r.mismatches);
  }
  return r;
}

static Result scan_int_bf16(const std::string& name,int lo,int hi) {
  Result r{name,"literal_exhaustive_raw_pairs",0,static_cast<uint64_t>(hi-lo+1)*65536ull,0};
  for(int a=lo;a<=hi;++a) {
    FPOperand ai{a<0,std::abs(a),0,a==0,false,false};
    for(uint32_t b=0;b<65536;++b)
      verify(r.mode,product(ai,decode_bf16(static_cast<uint16_t>(b)),false),product(ai,decode_bf16(static_cast<uint16_t>(b)),true),r.checks,r.mismatches);
  }
  return r;
}

static Result scan_bf16_equivalence(std::vector<std::tuple<std::string,size_t,size_t,uint64_t>>& families) {
  Result r{"bf16_bf16","complete_equivalence_class_proof",0,1ull<<32,0};
  auto nn=product_set(128,255,128,255);
  auto sn=product_set(1,127,128,255);
  auto ss=product_set(1,127,1,127);
  struct Fam { std::string name; const std::set<uint32_t>* products; int lo; int hi; };
  std::array<Fam,3> fs{{{"normal_normal",&nn,-266,240},{"subnormal_normal",&sn,-266,-13},{"subnormal_subnormal",&ss,-266,-266}}};
  for(const auto& f:fs) {
    uint64_t before=r.checks;
    for(auto p:*f.products) for(int scale=f.lo;scale<=f.hi;++scale) for(int sign=0;sign<2;++sign)
      verify(f.name,pack_rtl(sign,p,scale),pack_reference(sign,p,scale),r.checks,r.mismatches);
    uint64_t count=r.checks-before;
    families.emplace_back(f.name,f.products->size(),static_cast<size_t>(f.hi-f.lo+1),count);
    r.finite_equivalence_checks+=count;
  }
  std::array<uint16_t,10> reps{{0x0000,0x8000,0x0001,0x8001,0x3f80,0xbf80,0x7f80,0xff80,0x7fc1,0xffc1}};
  for(auto a:reps) for(auto b:reps) {
    verify("bf16_special",product(decode_bf16(a),decode_bf16(b),false),product(decode_bf16(a),decode_bf16(b),true),r.checks,r.mismatches);
    ++r.special_representative_checks;
  }
  return r;
}

int main(int argc,char** argv) {
  fs::path out="results";
  if(argc==3 && std::string(argv[1])=="--output-dir") out=argv[2];
  fs::create_directories(out);
  std::vector<Result> rows;
  rows.push_back(scan_i4_i8());
  rows.push_back(scan_i8_i8());
  rows.push_back(scan_fp8_fp8());
  rows.push_back(scan_i4_fp8());
  rows.push_back(scan_int_bf16("i4_bf16",-8,7));
  rows.push_back(scan_int_bf16("i8_bf16",-128,127));
  std::vector<std::tuple<std::string,size_t,size_t,uint64_t>> families;
  rows.push_back(scan_bf16_equivalence(families));

  uint64_t checks=0,space=0,mismatches=0;
  std::ofstream csv(out/"full_input_domain_summary.csv");
  csv << "mode,coverage_kind,checks,finite_equivalence_checks,special_representative_checks,mismatches,raw_pair_space\n";
  for(const auto& r:rows) {
    csv<<r.mode<<','<<r.coverage_kind<<','<<r.checks<<','<<r.finite_equivalence_checks<<','<<r.special_representative_checks<<','<<r.mismatches<<','<<r.raw_pair_space<<"\n";
    checks+=r.checks; space+=r.raw_pair_space; mismatches+=r.mismatches;
  }

  std::ofstream js(out/"full_input_domain_report.json");
  js << "{\n  \"status\": \""<<(mismatches?"FAIL":"PASS")<<"\",\n"
     << "  \"literal_or_equivalence_checks\": "<<checks<<",\n"
     << "  \"raw_pair_space_covered\": "<<space<<",\n"
     << "  \"mismatches\": "<<mismatches<<",\n"
     << "  \"bf16_raw_pair_space\": 4294967296,\n"
     << "  \"bf16_finite_equivalence_families\": [\n";
  for(size_t i=0;i<families.size();++i) {
    auto [name,p,s,c]=families[i];
    js << "    {\"family\":\""<<name<<"\",\"unique_significand_products\":"<<p<<",\"scale_sums\":"<<s<<",\"product_signs\":2,\"checks\":"<<c<<"}"<<(i+1<families.size()?",":"")<<"\n";
  }
  js << "  ],\n"
     << "  \"bf16_proof\": \"Every finite nonzero BF16 raw pair is classified by sign XOR, 8-bit significand product, and scale-exponent sum. Significand and exponent fields are independent; the scanned normal-normal, subnormal-normal, and subnormal-subnormal families cover every reachable finite class. Zero, Inf, and NaN category/sign combinations are separately enumerated.\",\n"
     << "  \"sequence_space_note\": \"All scalar input pairs are covered. Arbitrary accumulator sequences are unbounded and are verified separately with bounded exhaustive and adversarial long-K tests.\"\n}\n";
  std::cout << "checks="<<checks<<" raw_pair_space="<<space<<" mismatches="<<mismatches<<"\n";
  return mismatches?2:0;
}
