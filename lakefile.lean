import Lake
open Lake DSL

package «ginac-lean» {
  -- add package configuration options here
}

lean_lib «GinacLean» {
  -- add library configuration options here
}

@[default_target]
lean_exe «ginac-lean» {
  root := `Main
}
