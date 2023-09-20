import Lake
open System Lake DSL

package «ginac-lean» where
  srcDir := "lean"
  precompileModules := true
  -- preferReleaseBuild := get_config? noCloudRelease |>.isNone
  buildType := BuildType.debug
  -- buildArchive? := is_arm? |>.map (if · then "arm64" else "x86_64")
  moreLinkArgs := #[s!"-L{__dir__}/build/lib", "-lcln", "-lginac", "-lstdc++"]
  weakLeanArgs := #[
    s!"--load-dynlib={__dir__}/build/lib/" ++ nameToSharedLib "cln",
    s!"--load-dynlib={__dir__}/build/lib/" ++ nameToSharedLib "ginac"
  ]

lean_lib «GinacLean» {
  -- add library configuration options here
}

lean_lib «GinacFFI» {
  -- add library configuration options here
}

@[default_target]
lean_exe «ginac-lean» {
  root := `Main
}

def afterReleaseSync (pkg : Package) (build : SchedulerM (Job α)) : IndexBuildM (Job α) := do
  if pkg.preferReleaseBuild ∧ pkg.name ≠ (← getRootPackage).name then
    (← pkg.release.fetch).bindAsync fun _ _ => build
  else
    build

def afterReleaseAsync (pkg : Package) (build : BuildM α) : IndexBuildM (Job α) := do
  if pkg.preferReleaseBuild ∧ pkg.name ≠ (← getRootPackage).name then
    (← pkg.release.fetch).bindSync fun _ _ => build
  else
    Job.async build

target libcln pkg : FilePath := do
  afterReleaseAsync pkg do
    let dst := pkg.nativeLibDir / (nameToSharedLib "cln")
    createParentDirs dst
    let depTrace := Hash.ofString dst.toString
    let trace ← buildFileUnlessUpToDate dst depTrace do
      proc {
        cmd := "echo"
        args := #["Looking for", dst.toString]
      }
    return (dst, trace)

target libginac pkg : FilePath := do
  afterReleaseAsync pkg do
    let dst := pkg.nativeLibDir / (nameToSharedLib "ginac")
    createParentDirs dst
    let depTrace := Hash.ofString dst.toString
    let trace ← buildFileUnlessUpToDate dst depTrace do
      proc {
        cmd := "echo"
        args := #["Looking for", dst.toString]
      }
    return (dst, trace)

def buildCpp (pkg : Package) (path : FilePath) (deps : List (BuildJob FilePath)) : SchedulerM (BuildJob FilePath) := do
  let optLevel := if pkg.buildType == .release then "-O3" else "-O0"
  let mut flags := #[
    "-fPIC",
    "-std=c++11",
    -- "-lstdc++",
    -- "-stdlib=libc++",
    -- "-I", (← getLeanIncludeDir).toString,
    -- "-I", (pkg.buildDir / "include").toString,
    -- "-L", (pkg.buildDir / "lib").toString,
    -- "-lcln",
    -- "-lginac",
    optLevel
  ]
  match get_config? targetArch with
  | none => pure ()
  | some arch => flags := flags.push s!"--target={arch}"
  let args := flags ++ #["-I", (← getLeanIncludeDir).toString, "-I", (pkg.buildDir / "include").toString]
  let oFile := pkg.buildDir / (path.withExtension "o")
  let srcJob ← inputFile <| pkg.dir / path
  buildFileAfterDepList oFile (srcJob :: deps) (extraDepTrace := computeHash flags) fun deps =>
    compileO path.toString oFile deps[0]! args "clang++"

target ginac_ffi.o pkg : FilePath := do
  -- let oFile := pkg.buildDir / "cpp" / "ginac_ffi.o"
  -- let srcJob ← inputFile <| pkg.dir / "cpp" / "ginac_ffi.cpp"
  -- let flags := #[
  --   "-fPIC",
  --   "-std=c++11",
  --   "-I", (← getLeanIncludeDir).toString,
  --   "-I", (pkg.buildDir / "installed" / "include").toString,
  --   "-L", (pkg.buildDir / "installed" / "lib").toString,
  --   "-l", "cln",
  --   "-l", "ginac"
  --   ]
  let cln ← libcln.fetch
  let ginac ← libginac.fetch
  let build := buildCpp pkg "cpp/ginac_ffi.cpp" [cln, ginac]
  afterReleaseSync pkg build
  -- buildO "ginac_ffi.cpp" oFile srcJob flags "c++"

extern_lib libginacffi pkg := do
  let name := nameToStaticLib "ginacffi"
  let ffiO ← ginac_ffi.o.fetch
  buildStaticLib (pkg.nativeLibDir / name) #[ffiO]