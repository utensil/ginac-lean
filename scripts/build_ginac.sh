#!/bin/bash

SCRIPTS_DIR=$(realpath "$(dirname "$0")")
WORKSPACES=$(realpath "$(dirname "$0")/../build")
INSTALLED_DIR=$WORKSPACES

mkdir -p $WORKSPACES/
mkdir -p $INSTALLED_DIR/

show_warning()
{
    echo -e "\e[31mWARN\e[0m" "$@"
}

show_info()
{
    echo -e "\e[34mINFO\e[0m" "$@"
}

show_debug()
{
    echo -e "\e[90mDEBUG\e[0m" "$@"
}

show_ok()
{
    echo -e "\e[32mOK\e[0m" "$@"
}

download()
{
    URL=$1
    TAR=$(basename "$URL")
    DIR=${2:-${TAR%.t*}}

    if [ ! -f "$WORKSPACES/$TAR" ]; then
        echo "Downloading to $WORKSPACES/$TAR"
        wget --no-check-certificate "$URL" -O "$WORKSPACES/$TAR"
    else
        echo "Found downloaded $WORKSPACES/$TAR"
    fi

    if [ ! -d "$WORKSPACES/$DIR" ]; then
        echo "Extracting to "$WORKSPACES/$DIR", this may take a while..."
        tar -xf "$WORKSPACES/$TAR" -C $WORKSPACES/
    else
        echo "Found extracted $WORKSPACES/$DIR"
    fi

    # declare -g INSTALLED_DIR="$WORKSPACES/$DIR"
}

mkdir -p $WORKSPACES
cd $WORKSPACES

LIBCLN=cln-1.3.6

download https://www.ginac.de/CLN/$LIBCLN.tar.bz2

export CC="clang"
export CXX="clang++"
export CPPFLAGS="-DNO_ASM -stdlib=libc++"

cd $LIBCLN

# On mac, `arch -x86_64 bash scripts/build_ginac.sh` gets further but still fails

# Fix issues on Mac M1
# inspired by https://www.ginac.de/pipermail/cln-list/2021-April/000793.html
# created by diff -u src/base/low/cl_low_div_old.cc src/base/low/cl_low_div.cc > cl_low_div.patch
patch -N src/base/low/cl_low_div.cc < $SCRIPTS_DIR/cl_low_div.patch
# created by diff -u src/base/low/cl_low_mul_old.cc src/base/low/cl_low_mul.cc > cl_low_mul.patch
patch -N src/base/low/cl_low_mul.cc < $SCRIPTS_DIR/cl_low_mul.patch

# error: macho does not support linking multiple objects into one

./configure --prefix=$INSTALLED_DIR && make -j8

# make  check-TESTS
# PASS: exam
# ../build-aux/test-driver: line 107: 42223 Abort trap: 6           "$@" > $log_file 2>&1
# FAIL: tests
# ============================================================================
# Testsuite summary for cln 1.3.6
# ============================================================================
# # TOTAL: 2
# # PASS:  1
# # SKIP:  0
# # XFAIL: 0
# # FAIL:  1
# # XPASS: 0
# # ERROR: 0
# ============================================================================
# See tests/test-suite.log
# ============================================================================
make check

make install

cd $WORKSPACES

download https://www.ginac.de/ginac-1.8.7.tar.bz2

cd ginac-1.8.7

export CLN_CFLAGS="-I$INSTALLED_DIR/include"
export CLN_LIBS="-L$INSTALLED_DIR/lib -lcln"

./configure  --prefix=$INSTALLED_DIR && make -j8

# make  check-TESTS
# PASS: exam_paranoia
# PASS: exam_heur_gcd
# PASS: exam_match
# PASS: exam_parser
# PASS: exam_numeric
# PASS: exam_relational
# PASS: exam_powerlaws
# PASS: exam_collect
# PASS: exam_inifcns
# PASS: exam_inifcns_nstdsums
# PASS: exam_inifcns_elliptic
# PASS: exam_differentiation
# PASS: exam_polygcd
# PASS: exam_collect_common_factors
# PASS: exam_normalization
# PASS: exam_sqrfree
# PASS: exam_factor
# PASS: exam_pseries
# PASS: exam_matrices
# PASS: exam_lsolve
# PASS: exam_indexed
# PASS: exam_color
# FAIL: exam_clifford
# FAIL: exam_archive
# PASS: exam_structure
# PASS: exam_misc
# PASS: exam_pgcd
# PASS: exam_mod_gcd
# PASS: exam_chinrem_gcd
# PASS: exam_function_exvector
# PASS: exam_real_imag
# PASS: check_numeric
# PASS: check_inifcns
# PASS: check_matrices
# PASS: check_lsolve
# PASS: check_cra
# PASS: time_dennyfliegner
# PASS: time_gammaseries
# PASS: time_vandermonde
# PASS: time_toeplitz
# PASS: time_lw_A
# PASS: time_lw_B
# PASS: time_lw_C
# PASS: time_lw_D
# PASS: time_lw_E
# PASS: time_lw_F
# PASS: time_lw_G
# PASS: time_lw_H
# PASS: time_lw_IJKL
# PASS: time_lw_M1
# PASS: time_lw_M2
# PASS: time_lw_N
# PASS: time_lw_O
# PASS: time_lw_P
# PASS: time_lw_Pprime
# PASS: time_lw_Q
# PASS: time_lw_Qprime
# PASS: time_antipode
# PASS: time_fateman_expand
# PASS: time_uvar_gcd
# PASS: time_parser
# ============================================================================
# Testsuite summary for GiNaC 1.8.7
# ============================================================================
# # TOTAL: 61
# # PASS:  59
# # SKIP:  0
# # XFAIL: 0
# # FAIL:  2
# # XPASS: 0
# # ERROR: 0
make check

make install

echo Add the following to your ~/.profile or similar files that applies to your shell
echo export PATH=$INSTALLED_DIR/bin:$PATH
