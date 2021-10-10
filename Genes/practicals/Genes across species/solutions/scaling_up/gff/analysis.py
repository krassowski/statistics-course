import pandas
from .parse import gff3_to_dataframe
from .sequences import sequences_from_gff3_metadata
from .summary import summarise_transcripts_and_exons_per_gene
from .regions import compute_genome_bases_covered

class GFF3:
    def __init__( self, filename, analysis ):
        self.filename = filename
        self.analysis = analysis
        data = self.load_and_sanitise_data()

        print( "++ Extracting regular protein-coding genes..." )
        self.m_genes = data[ (data['type'] == 'gene') & (data['biotype'] == 'protein_coding') ]
        self.m_transcripts = data[ (data['type'] == 'mRNA') & (data['Parent'].isin( self.m_genes['ID'] ))]
        self.m_exons = data[ (data['type'] == 'exon') & (data['Parent'].isin( self.m_transcripts['ID'] ))]
        self.m_cds = data[ (data.type == 'CDS') & (data['Parent'].isin( self.m_transcripts['ID'] ))]
        # The above is a common pattern: I want to have methods called genes(),
        # transcripts() etc. below. So to avoid name clashes, the data members
        # are called m_genes, m_transcripts etc.

        self.add_gene_summary_columns()

        print( "++ loading sequences..." )
        self.m_sequences = self.load_sequences( filename )

    def load_and_sanitise_data( self, filename ):
        print( "++ GFF3: Loading data from %s..." % filename )
        result = gff3_to_resultframe( open( filename ) )
        result.insert( 0, 'analysis', self.analysis )
        print( "++ ok, %d records loaded." % result.shape[0] )
        # Remove unwanted parts of IDs: the "gene:" and "transcript:" prefixes
        def fix_id( id ):
            if id is None:
                return None
            else:
                return id.replace( "gene:", "" ).replace( "transcript:", "" )
        result.loc[ :, 'ID'] = result['ID'].apply( fix_id )
        result.loc[ :, 'Parent'] = result['Parent'].apply( fix_id )
        # Kludge: fix gene types/biotypes for PlasmoDB result
        result.loc[result.type == 'protein_coding_gene', 'biotype' ] = 'protein_coding'
        result.loc[result.type == 'protein_coding_gene', 'type' ] = 'gene'
        return result

    def add_gene_summary_columns( self ):
        # We add columns to genes from the gene summary.
        # Another way would be to make summarise_transcripts_and_exons_per_gene() return all this info, but that seems wasteful.
        print( "++ summarising genes..." )
        per_gene_summary = summarise_transcripts_and_exons_per_gene( self.m_genes, self.m_transcripts, self.m_exons )
        self.m_genes = pandas.merge(
            self.m_genes,
            per_gene_summary[['ID', 'number_of_transcripts', 'average_number_of_exons']],
            left_on = 'ID',
            right_on = 'ID'
        )
        self.m_genes.loc[ :, 'length'] = self.m_genes['end'] - self.m_genes['start'] + 1

    def load_sequences( self, filename ):
        print( "++ loading sequences..." )
        result = sequences_from_gff3_metadata( open( filename ) )
        result.insert( 0, 'analysis', self.analysis )
        result.insert( result.shape[1], 'sequence_length', result['end'] - result['start'] + 1 )
        return result

    def genes( self ):
        columns = [
            "analysis",
            "ID",
            "Parent",
            "Name",
            "biotype",
            "seqid",
            "source",
            "start",
            "end",
            "strand",
            "attributes",
            "number_of_transcripts",
            "average_number_of_exons"
        ]
        return self.m_genes[ columns ]

    def transcripts( self ):
        columns = [
            "analysis",
            "ID",
            "Parent",
            "biotype",
            "seqid",
            "source",
            "start",
            "end",
            "strand",
            "attributes"
        ]
        return self.m_transcripts[ columns ]

    def exons( self ):
        columns = [
            "analysis",
            "ID",
            "Parent",
            "biotype",
            "seqid",
            "source",
            "start",
            "end",
            "strand"
        ]
        return self.m_exons[ columns ]

    def cds( self ):
        columns = [
            "analysis",
            "ID",
            "Parent",
            "biotype",
            "seqid",
            "source",
            "start",
            "end",
            "strand"
        ]
        return self.m_cds[ columns ]

    def sequences( self ):
        return self.m_sequences

    def compute_gene_statistics( self ):
        import pandas
        result = self.m_genes[ self.m_genes['biotype'] == 'protein_coding' ].groupby( 'analysis' ).agg(
            total_genes = pandas.NamedAgg(
                column = 'ID',
                aggfunc = lambda x: x.notnull().sum()
            ),
            total_single_exon_genes = pandas.NamedAgg(
                column = 'average_number_of_exons',
                aggfunc = lambda x: ( x == 1 ).sum()
            ),
            proportion_single_exon_genes = pandas.NamedAgg(
                column = 'average_number_of_exons',
                aggfunc = lambda x: (x == 1).sum() / x.notnull().sum()
            ),
            longest_gene = pandas.NamedAgg(
                column = "length",
                aggfunc = lambda x: x.max()
            ),
            shortest_gene = pandas.NamedAgg(
                column = "length",
                aggfunc = lambda x: x.min()
            ),
            highest_exon_count = pandas.NamedAgg(
                column = "average_number_of_exons",
                aggfunc = lambda x: x.max()
            ),
            highest_transcript_count = pandas.NamedAgg(
                column = "number_of_transcripts",
                aggfunc = lambda x: x.max()
            )
        )
        return result

    def compute_coverage_statistics( self ):
        """Compute the protein-coding gene, exon, and cds genome coverage"""
        import pandas
        
        def compute_coverages( genes, exons, cds, sequences ):
            # the .reset_index() is used here to turn the analysis column back into a normal column.
            # (otherwise it is an 'index' and behaves differently)
            result = {
                "genes": compute_genome_bases_covered( genes, sequences ).reset_index(),
                "exons": compute_genome_bases_covered( exons, sequences ).reset_index(),
                "cds": compute_genome_bases_covered( cds, sequences ).reset_index()
            }
            return result
        
        def build_single_table( coverages ):
            # Now build a single table
            result = coverages['genes'][['analysis', 'sequence_length']]
            for what in [ 'genes', 'exons', 'cds' ]:
                result = pandas.merge(
                    result,
                    coverages[what][['analysis', 'bases_covered', 'proportion' ]],
                    left_on = 'analysis',
                    right_on = 'analysis'
                )
                result.rename(
                    columns = {
                        "bases_covered": "%s:bases_covered" % what,
                        "proportion": "%s:proportion_covered" % what
                    },
                    inplace = True
                )
            return result

        coverages = compute_coverages( self.m_genes, self.m_exons, self.m_cds, self.m_sequences )
        return build_single_table( coverages )
