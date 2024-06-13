# Create an array of all entities
[
    # The top-level is just a translation unit
    .inner[]
    # Here we assume all meaningful entities are in namespace GiNaC
    |select(.kind=="NamespaceDecl" and .name=="GiNaC")
    |.inner[]
    # We will only process what's defined in the current header, not included headers
    |select(.loc|has("includedFrom")|not)
    # Remove some unwanted fields
    |del(..|.loc?)|del(..|.range?)|del(..|.id?)
    # For debug, remove .inner beyond 2nd level 
    # so we keep only class, method, but not arguments and their types
    # |del(.inner?|.[]?|.inner?)
    # Alternatively, remove .inner beyond 3nd level 
    # i.e. keep only class, method, arguments but not their types
    |del(.inner?|.[]?|.inner?|.[]?|.inner?)
    |select(
        # ..|
        (.kind?=="TypedefDecl") or
        (.kind?=="CXXRecordDecl" and .tagUsed? == "struct" and has("inner")) or
        (.kind?=="CXXRecordDecl" and .tagUsed? == "class" and has("inner")) or true
    )   
]
