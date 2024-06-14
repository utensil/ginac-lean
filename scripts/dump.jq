# Create an array of all entities
[
    # The top-level is just a translation unit
    .inner[]
    # Here we assume all meaningful entities are in namespace GiNaC or cln
    |select(.kind=="NamespaceDecl" and (.name=="GiNaC" or .name=="cln"))
    |.inner[]
    # We will only process what's defined in the current header, not included headers
    |select(.loc|has("includedFrom")|not)
    # debug doesn't work in jaq, and the output is huge if I use jq
    # |select(..|has("loc"))| .[] as $loc| debug("loc = \($loc)", .)
    # Remove some unwanted fields
    |del(..|.id?)
    |del(..|.range?)
    |del(..|.loc?|.expansionLoc?)
    # convert the absolute include path to a relative one
    |(..|.loc?|.spellingLoc?|.includedFrom?)|=(.file?|split("/include/")|.[-1])
    |del(..|.loc?|.spellingLoc?|.offset?, .line?, .col?, .tokLen?, .file?)
    # it seems that "loc: null" is everywhere, so remove it
    |del(..|.loc?|select(.==null))
    # |del(..|.loc?)
    # for debug tidy
    # For debug, remove .inner beyond 2nd level 
    # so we keep only class, method, but not arguments and their types
    # |del(.inner?|.[]?|.inner?)
    # Alternatively, remove .inner beyond 3nd level 
    # i.e. keep only class, method, arguments but not their types
    # |del(.inner?|.[]?|.inner?|.[]?|.inner?)
    # Remove all inner fields of ParmVarDecl
    |del(..|select(.kind?=="ParmVarDecl")|.[]?|.inner?)
    |select(
        # ..|
        (.kind?=="TypedefDecl")
        or (.kind?=="CXXRecordDecl" and .tagUsed? == "struct" and has("inner"))
        or (.kind?=="CXXRecordDecl" and .tagUsed? == "class" and has("inner"))
        or (.kind?=="FunctionTemplateDecl")
        or (.kind?=="CXXConstructorDecl")
        or (.kind?=="CXXMethodDecl")
        or (.kind?=="FunctionDecl")
        # for debug what's left
        # | not
        # for debug what's all
        # or true
    )
    |del(..|select(
        (.kind?=="DeclStmt")
        or (.kind?=="IfStmt")
        or (.kind?=="NullStmt")
        or (.kind?=="CompoundStmt")
        or (.kind?=="CXXCtorInitializer")
    ))
    # for debug tidy
    #|del(..|.inner?)
]
