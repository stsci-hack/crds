"""This module is a command line script which lists the match tuples associated
with a reference file.

% python -m crds.matches  --contexts hst_0001.pmap --files lc41311jj_pfl.fits
lc41311jj_pfl.fits : ACS PFLTFILE DETECTOR='WFC' CCDAMP='A|ABCD|AC|AD|B|BC|BD|C|D' FILTER1='F625W' FILTER2='POL0V' OBSTYPE='IMAGING' FW1OFFST='N/A' FW2OFFST='N/A' FWSOFFST='N/A' DATE-OBS='1997-01-01' TIME-OBS='00:00:00'

A number of command line switches control output formatting.

The api function find_full_match_paths() returns a list of "match paths",  lists of parkey value assignment tuples:
"""
import os.path
from pprint import pprint as pp

from crds import rmap, log, cmdline


# ===================================================================

def test():
    """Run any doctests."""
    import doctest, crds.matches
    return doctest.testmod(crds.matches)

# ===================================================================

def find_full_match_paths(context, reffile):
    """Return the list of full match paths for `reference` in `context` as a
    list of tuples of tuples.   Each inner tuple is a (var, value) pair.
    
    Returns [((context_tuples,),(match_tuple,),(useafter_tuple,)), ...]
    
    >>> pp(find_full_match_paths("hst.pmap", "q9e1206kj_bia.fits"))    
    [((('observatory', 'hst'), ('instrument', 'acs'), ('filekind', 'biasfile')),
      (('DETECTOR', 'HRC'),
       ('CCDAMP', 'A'),
       ('CCDGAIN', '4.0'),
       ('APERTURE', '*'),
       ('NAXIS1', '<=2048'),
       ('NAXIS2', '1044.0'),
       ('LTV1', '19.0'),
       ('LTV2', '20.0'),
       ('XCORNER', 'N/A'),
       ('YCORNER', 'N/A'),
       ('CCDCHIP', 'N/A')),
      (('DATE-OBS', '2006-07-04'), ('TIME-OBS', '11:32:35')))]
    """
    ctx = rmap.asmapping(context, cached=True)
    return ctx.file_matches(reffile)

def find_match_paths_as_dict(context, reffile):
    """Return the matching parameters for reffile as a list of dictionaries, one dict for
    each match case giving the parameters of that match.

    >>> pp(find_match_paths_as_dict("hst.pmap", "q9e1206kj_bia.fits"))
    [{'APERTURE': '*',
      'CCDAMP': 'A',
      'CCDCHIP': 'N/A',
      'CCDGAIN': '4.0',
      'DATE-OBS': '2006-07-04',
      'DETECTOR': 'HRC',
      'LTV1': '19.0',
      'LTV2': '20.0',
      'NAXIS1': '<=2048',
      'NAXIS2': '1044.0',
      'TIME-OBS': '11:32:35',
      'XCORNER': 'N/A',
      'YCORNER': 'N/A',
      'filekind': 'biasfile',
      'instrument': 'acs',
      'observatory': 'hst'}]
    """
    matches = find_full_match_paths(context, reffile)
    return [ _flatten_items_to_dict(match) for match in matches ]

def _flatten_items_to_dict(match_path):
    """Given a `match_path` which is a sequence of parameter items and sub-paths,  return
    a flat dictionary representation:
    
    returns   { matchinhg_par:  matching_par_value, ...}
    """
    result = {}
    for par in match_path:
        if len(par) == 2 and isinstance(par[0], basestring) and isinstance(par[1], basestring):
            result[par[0]] = par[1]
        else:
            result.update(_flatten_items_to_dict(par))
    return result

def get_minimum_exptime(context, references):
    """Return the minimum EXPTIME for the list of `references` with respect to `context`.
    This is used to define the potential reprocessing impact of new references,  since
    no dataset with an earlier EXPTIME than a reference is typically affected by the 
    reference,  partciularly with respect to the HST USEAFTER approach.
    
    >>> get_minimum_exptime("hst.pmap", ["q9e1206kj_bia.fits"])
    '2006-07-04 11:32:35'
    """
    return min([_get_minimum_exptime(context, ref) for ref in references])

def _get_minimum_exptime(context, reffile):
    """Given a `context` and a `reffile` in it,  return the minimum EXPTIME for all of
    it's match paths constructed from DATE-OBS and TIME-OBS.
    """
    path_dicts = find_match_paths_as_dict(context, reffile)
    exptimes = [ get_exptime(path_dict) for path_dict in path_dicts ]
    return min(exptimes)

def get_exptime(match_dict):
    """Given a `match_dict` dictionary of matching parameters for one match path,
    return the EXPTIME for it or 1900-01-01 00:00:00 if no EXPTIME can be derived.
    """
    if "DATE-OBS" in match_dict and "TIME-OBS" in match_dict:
        return match_dict["DATE-OBS"] + " " + match_dict["TIME-OBS"]
    elif "META.OBSERVATION.DATE" in match_dict:
        return match_dict["META.OBSERVATION.DATE"]
    else:
        return "1900-01-01 00:00:00"        

# ===================================================================

class MatchesScript(cmdline.ContextsScript):
    """Command line script for printing reference selection criteria."""

    description = """
Prints out the selection criteria by which the specified references are matched
with respect to a particular context.
    """

    epilog = """
crds.matches can be invoked like this:

% python -m crds.matches  --contexts hst_0001.pmap --files lc41311jj_pfl.fits
lc41311jj_pfl.fits : ACS PFLTFILE DETECTOR='WFC' CCDAMP='A|ABCD|AC|AD|B|BC|BD|C|D' FILTER1='F625W' FILTER2='POL0V' DATE-OBS='1997-01-01' TIME-OBS='00:00:00'

% python -m crds.matches --contexts hst.pmap --files lc41311jj_pfl.fits --omit-parameter-names --brief-paths
lc41311jj_pfl.fits :  'WFC' 'A|ABCD|AC|AD|B|BC|BD|C|D' 'F625W' 'POL0V' '1997-01-01' '00:00:00'

% python -m crds.matches --contexts hst.pmap --files lc41311jj_pfl.fits --tuple-format
lc41311jj_pfl.fits : (('OBSERVATORY', 'HST'), ('INSTRUMENT', 'ACS'), ('FILEKIND', 'PFLTFILE'), ('DETECTOR', 'WFC'), ('CCDAMP', 'A|ABCD|AC|AD|B|BC|BD|C|D'), ('FILTER1', 'F625W'), ('FILTER2', 'POL0V'), ('DATE-OBS', '1997-01-01'), ('TIME-OBS', '00:00:00'))


"""
    
    def add_args(self):
        super(MatchesScript, self).add_args()
        self.add_argument("--files", nargs="+", 
            help="References for which to dump selection criteria.")
        self.add_argument("-b", "--brief-paths", action="store_true",
            help="Don't the instrument and filekind.")
        self.add_argument("-o", "--omit-parameter-names", action="store_true",
            help="Hide the parameter names of the selection criteria,  just show the values.")
        self.add_argument("-t", "--tuple-format", action="store_true",
            help="Print the match info as Python tuples.")

    def main(self):
        """Process command line parameters in to a context and list of
        reference files.   Print out the match tuples within the context
        which contain the reference files.
        """
        for ref in self.files:
            cmdline.reference_file(ref)
        for context in self.contexts:
            self.dump_match_tuples(context)
            
    def locate_file(self, file):
        """Override for self.files..."""
        return os.path.basename(file)
    
    def dump_match_tuples(self, context):
        """Print out the match tuples for `references` under `context`.
        """
        ctx = context if len(self.contexts) > 1 else ""  
        for ref in self.files:
            matches = self.find_match_tuples(context, ref)
            if matches:
                for match in matches:        
                    log.write(ctx, ref, ":", match)
            else:
                log.write(ctx, ref, ":", "none")

    def find_match_tuples(self, context, reffile):
        """Return the list of match representations for `reference` in `context`.   
        """
        ctx = rmap.get_cached_mapping(context)
        matches = ctx.file_matches(reffile)
        result = []
        for path in matches:
            prefix = self.format_prefix(path[0])
            match_tuple = tuple([self.format_match_tup(tup) for section in path[1:] for tup in section])
            if self.args.tuple_format:
                if prefix:
                    match_tuple = prefix + match_tuple
            else:
                match_tuple = prefix + " " + " ".join(match_tuple)    
            result.append(match_tuple)
        return result
    
    def format_prefix(self, path):
        """Return any representation of observatory, instrument, and filekind."""
        if not self.args.brief_paths:
            if self.args.tuple_format:
                prefix = tuple([tuple([t.upper() for t in tup]) for tup in path])
            else:
                prefix = " ".join(tup[1].upper() for tup in path[1:])
        else:
            prefix = ""
        return prefix 

    def format_match_tup(self, tup):
        """Return the representation of the selection criteria."""
        if self.args.tuple_format:
            return tup if not self.args.omit_parameter_names else tup[1]
        else:
            tup = tup[0], repr(tup[1])
            return "=".join(tup if not self.args.omit_parameter_names else tup[1:])
        
if __name__ == "__main__":
    MatchesScript()()
